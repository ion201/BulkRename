#!/usr/bin/python3

import sys
import os
import re
import tkinter as tk
from io import StringIO
import traceback
import shutil

VERSION = '1.0'
URL = 'https://github.com/ion201/'

MAX_SHOWN_FILES = 20


def AddExitBindings(widget):
    widget.event_add('<<close>>', '<KeyPress-Escape>')
    widget.bind('<<close>>', PleaseExit)


def TkGetUserInput(text, events, exitBinding=True):
    global form_data
    form_data = None

    tk_root = tk.Tk()
    tk_root.title('Batch Rename v%s' % VERSION)

    tk.Label(tk_root, text=text).pack()

    if exitBinding:
        AddExitBindings(tk_root)

    inputBox = tk.Entry(tk_root)
    # inputBox.insert(0, filename)
    # inputBox.select_to(tk.END)
    inputBox.focus_set()
    for funcName, keyCode in events:
        inputBox.event_add('<<%s>>' % funcName, '<%s>' % keyCode)
        inputBox.bind('<<%s>>' % funcName, globals()[funcName])
        inputBox.pack()

    tk_root.mainloop()


def DestroyRoot(thing):
    if isinstance(thing, tk.Event):
        widget = thing.widget
    else:
        widget = thing
    widget._nametowidget(widget.winfo_parent()).destroy()

def PleaseExit(event):
    DestroyRoot(event)
    sys.exit(0)


def submitFindStrPlain(event):
    global form_data
    form_data = re.escape(event.widget.get())
    DestroyRoot(event)

def submitFindStrRegex(event):
    global form_data
    form_data = event.widget.get()
    DestroyRoot(event)

def submitReplacementStr(event):
    global form_data
    form_data = event.widget.get()
    DestroyRoot(event)

def ConfirmRename(event):
    global form_data
    form_data = True
    DestroyRoot(event)

def DialogText(text):
    tk_root = tk.Tk()
    tk_root.title('Message')
    AddExitBindings(tk_root)
    tk.Label(tk_root, text=text).pack()
    tk.Label(tk_root, text='\n Tap escape to close this dialog').pack()
    tk.mainloop()


def ProcessError(err):
    tb = err.__traceback__
    frame = tb.tb_frame

    s = StringIO()
    traceback.print_tb(tb, file=s)

    tk_root = tk.Tk()
    tk_root.title('Error')
    tk.Label(tk_root, text='Uncaught Exception! This shouldn\'t have happended.').pack()
    tk.Label(tk_root, text='If you can reproduce it, feel free to file an issue at:').pack()
    tk.Label(tk_root, text='%s' % URL).pack()
    tk.Label(tk_root, text='Please include a copy of this information:').pack()
    textbox = tk.Text(tk_root)
    textbox.insert('@0,0',
                    s.getvalue() + '\n' + \
                    str(frame.f_locals).replace(', ', '\n'))
    textbox.pack()

    tk_root.mainloop()


def main():
    # You shouldn't use global variables in your own code unless
    # you fully understand why this is a bad design decision :)
    global form_data

    files_old = []
    files_new = []

    for f in sys.argv[1:]:
        name = f.replace('file:///', '/')
        assert os.path.exists(name)
        files_old.append(name)

    files_old_tmp = [os.path.basename(f) for f in files_old]
    if len(files_old) > MAX_SHOWN_FILES:
        files_old_tmp = files_old_tmp[:MAX_SHOWN_FILES]
        files_old_tmp += ['And %d more...' % (len(files_old)-MAX_SHOWN_FILES)]
    prompt_1 = """Press <return> to process as plain text.
Press <shift+return> to process as regex.

Files queued:
%s""" % ('\n'.join(files_old_tmp))
    events_1 = [
        ('submitFindStrPlain', 'KeyPress-Return'),
        ('submitFindStrRegex', 'Shift-KeyPress-Return')
    ]

    prompt_2 = """Type the string to replace the first with.
Use "&" as a macro for the string being replaced. \& to insert the character only.
You'll get to see changes before they're made."""
    events_2 = [
        ('submitReplacementStr', 'KeyPress-Return')
    ]

    TkGetUserInput(prompt_1, events_1)
    if not form_data:
        DialogText('You need to type something in the box!')
        sys.exit(1)
    replace_exp = form_data

    TkGetUserInput(prompt_2, events_2)
    new_str = form_data

    for full_path in files_old:
        file_name = os.path.basename(full_path)

        # Use set to only get unique ones.
        matches = list(set(re.findall(replace_exp, file_name)))

        new_str_tmp = new_str

        if len(matches) == 1:
            # Yay! this one's easy
            new_str_tmp = matches[0].join(re.split(r'(?<!\\)&', new_str_tmp))
        else:
            # Not gonna touch this case yet.
            pass

        files_new.append(os.path.dirname(full_path) + '/' + \
                        new_str_tmp.join(re.split(replace_exp, file_name)))

    prompt_3 = "Files queued:\n"
    files_queued = 0
    for i in range(len(files_old)):
        # if i >= MAX_SHOWN_FILES:
        #     prompt_3 += 'And %d more...\n' % (len(files_old) - MAX_SHOWN_FILES)
        #     break
        if files_old[i] == files_new[i]:
            continue
        files_queued += 1
        prompt_3 += os.path.basename(files_old[i])
        prompt_3 += '  -->  '
        prompt_3 += os.path.basename(files_new[i])
        prompt_3 += '\n'
    if files_queued == 0:
        prompt_3 += 'No files matching pattern "%s" :(\n' % replace_exp
    prompt_3 += '\n'
    prompt_3 += '<Return> -- confirm.\n'
    prompt_3 += '<Escape> -- cancel and exit.\n'

    events_3 = [
        ('ConfirmRename', 'KeyPress-Return'),
    ]
    TkGetUserInput(prompt_3, events_3)

    print(form_data)


if __name__ == '__main__':
    try:
        main()
    except PermissionError as e:
        DialogText('You don\'t have permission to perform that operation!')
    except AssertionError as e:
        ProcessError(e)
