#!/usr/bin/env python3
##############################

VERSION = '1.0'
URL = 'https://github.com/ion201/BulkRename'

##############################

import sys
import os
import re
import tkinter as tk
from tkinter import font
from io import StringIO
import traceback
import shutil
try:
    from gi.repository import Gio
    gsettings = Gio.Settings('org.gnome.desktop.interface')
except ImportError:
    # Not a gnome based desktop. Use this default font
    gsettings = {'font-name': 'Cantarell 11'}


MAX_SHOWN_FILES = 200

W_WIDTH = 600
W_HEIGHT = 400


def AddExitBindings(widget, key_code='KeyPress-Escape'):
    widget.event_add('<<close>>', '<%s>' % key_code)
    widget.bind('<<close>>', PleaseExit)
    # If widget is a root, also bind any exit to PleaseExit()
    if isinstance(widget, tk.Tk):
        widget.protocol('WM_DELETE_WINDOW', PleaseExit)

def OnFrameConfigure(canvas):
    canvas.configure(scrollregion=canvas.bbox('all'))


def OnMousewheel(event, tk_canvas):
    print(event.delta)
    tk_canvas.yview_scroll(1, 'units')


def TkGetUserInput(tk_root, text, events, **label_kwargs):
    global form_data
    form_data = None

    tk_root.title('Batch Rename v%s' % VERSION)

    tk_frame = tk.Frame(tk_root)
    tk_canvas = tk.Canvas(tk_frame, width=W_WIDTH, height=W_HEIGHT)
    tk_subframe = tk.Frame(tk_canvas)
    tk_scroll = tk.Scrollbar(tk_frame, command=tk_canvas.yview)
    tk_label = tk.Label(tk_subframe, text=text, **label_kwargs)

    if tk_label.winfo_reqwidth() > W_WIDTH:
        tk_canvas.configure(width=tk_label.winfo_reqwidth())

    tk_canvas.configure(yscrollcommand=tk_scroll.set)
    tk_root.bind_all('<Button-4>',
        lambda event: tk_canvas.yview_scroll(-1, 'units'))
    tk_root.bind_all('<Button-5>',
        lambda event: tk_canvas.yview_scroll(1, 'units'))

    tk_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    tk_canvas.pack(expand=True)

    tk_canvas.create_window((0, 0), window=tk_subframe, anchor=tk.NW)
    tk_subframe.bind('<Configure>', lambda evt, canvas=tk_canvas: OnFrameConfigure(canvas))

    padding = int((tk_canvas.winfo_reqwidth() - tk_label.winfo_reqwidth()) / 2)
    tk.Frame(tk_subframe, width=padding).pack(fill=tk.Y, side=tk.LEFT)
    tk.Frame(tk_subframe, width=padding).pack(fill=tk.Y, side=tk.RIGHT)
    tk_label.pack(expand=True)

    tk_input_box = tk.Entry(tk_frame)
    tk_input_box.focus_set()
    for func_name, key_code in events:
        tk_input_box.event_add('<<%s>>' % func_name, '<%s>' % key_code)
        tk_input_box.bind('<<%s>>' % func_name, globals()[func_name])

    tk_input_box.pack(side=tk.BOTTOM)

    tk_frame.pack()

    tk_root.mainloop()


def DestroyParent(thing):
    if isinstance(thing, tk.Event):
        widget = thing.widget
    else:
        widget = thing
    parent = widget._nametowidget(widget.winfo_parent())
    tk_root = widget.winfo_toplevel()
    parent.destroy()
    tk_root.quit()


def PleaseExit(event=None):
    if event is not None:
        DestroyParent(event)
    sys.exit(0)


def submitFindStrPlain(event):
    global form_data
    form_data = re.escape(event.widget.get())
    DestroyParent(event)

def submitFindStrRegex(event):
    global form_data
    form_data = event.widget.get()
    DestroyParent(event)

def submitReplacementStr(event):
    global form_data
    form_data = event.widget.get()
    DestroyParent(event)

def ConfirmRename(event):
    global form_data
    form_data = True
    DestroyParent(event)

def DialogText(tk_root, text, **label_kwargs):
    tk_frame = tk.Frame(tk_root)
    tk_frame.pack()
    tk_root.title('Message')

    label = tk.Label(tk_frame, text=text, **label_kwargs)
    AddExitBindings(label, key_code='KeyPress-Return')
    label.pack()
    tk.Label(tk_frame, text='\n Tap escape or enter to close this dialog').pack()
    tk.mainloop()


def ProcessPermissionError(tk_root, err):
    s = StringIO()
    traceback.print_tb(err.__traceback__, file=s)
    message = "You don't have permssion to perform that operation!\n" + \
                "File: %s \n\nTraceback:\n%s" % (err.filename, s.getvalue())
    DialogText(tk_root, message, justify=tk.LEFT)


def ProcessFileNotFoundError(tk_root, err):
    s = StringIO()
    traceback.print_tb(err.__traceback__, file=s)
    message = "'%s' does not appear to exist!\n" % err + \
                "If you think this is a mistake,\n" + \
                "submit a bug report at %s\n\n" % URL + \
                "Traceback:\n" + \
                "%s" % s.getvalue()

    DialogText(tk_root, message, justify=tk.LEFT)


def ProcessUncaughtException(tk_root, err):
    tb = err.__traceback__
    frame = tb.tb_frame

    s = StringIO()
    traceback.print_tb(tb, file=s)

    tk_frame = tk.Frame(tk_root)
    tk_frame.pack()
    tk_root.title('Error')
    tk.Label(tk_frame, text='Uncaught Exception! This shouldn\'t have happended.').pack()
    tk.Label(tk_frame, text='If you can reproduce it, feel free to file an issue at:').pack()
    tk.Label(tk_frame, text='%s' % URL).pack()
    tk.Label(tk_frame, text='Please include a copy of this information:').pack()
    textbox = tk.Text(tk_frame)
    textbox.insert('@0,0',
                    s.getvalue() + '\n' + \
                    str(frame.f_locals).replace(', ', '\n'))
    textbox.pack()

    tk_root.mainloop()


def RenameFiles(files_old, files_new):
    assert len(files_old) == len(files_new)

    for old_path, new_path in zip(files_old, files_new):
        shutil.move(old_path, new_path)


def main(tk_root):
    # You shouldn't use global variables in your own code unless
    # you fully understand why this is a bad design decision :)
    global form_data

    AddExitBindings(tk_root)
    tk_root.minsize(width=W_WIDTH, height=W_HEIGHT)

    # Other options are 'document-font-name' and 'monospace-font-name'
    system_font = gsettings['font-name']
    font_size = int(re.findall('[0-9]*$', system_font)[0])
    font_family = re.findall('^[A-Za-z ]*', system_font)[0]

    default_font = font.nametofont('TkDefaultFont')
    default_font.configure(size=font_size, family=font_family)
    text_font = font.nametofont('TkTextFont')
    text_font.configure(size=font_size, family=font_family)

    files_old = []
    files_new = []

    for f in sys.argv[1:]:
        name = f.replace('file:///', '/')
        if not os.path.exists(name):
            raise FileNotFoundError(name)
        files_old.append(name)

    files_old_tmp = [os.path.basename(f) for f in files_old]
    if len(files_old) > MAX_SHOWN_FILES:
        files_old_tmp = files_old_tmp[:MAX_SHOWN_FILES]
        files_old_tmp += ['And %d more...' % (len(files_old)-MAX_SHOWN_FILES)]
    prompt_1 = """Press <return> to process as plain text.
Press <shift+return> to process as regex.

Files queued:
%s
""" % ('\n'.join(files_old_tmp))
    events_1 = [
        ('submitFindStrPlain', 'KeyPress-Return'),
        ('submitFindStrRegex', 'Shift-KeyPress-Return')
    ]

    prompt_2 = """Type the string to replace the first with.
Use "&" as a macro for the string being replaced.
\& to insert the character only.
You'll get to see changes before they're made.
"""
    events_2 = [
        ('submitReplacementStr', 'KeyPress-Return')
    ]

    TkGetUserInput(tk_root, prompt_1, events_1, justify=tk.LEFT)
    if not form_data:
        DialogText(tk_root, 'You need to type something in the box!')
        sys.exit(1)
    replace_exp = form_data

    TkGetUserInput(tk_root, prompt_2, events_2)
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
    files_old_filtered = []
    files_new_filtered = []
    for i in range(len(files_old)):
        if files_old[i] == files_new[i]:
            continue
        files_old_filtered.append(files_old[i])
        files_new_filtered.append(files_new[i])
        files_queued += 1
        prompt_3 += os.path.basename(files_old[i])
        prompt_3 += '  -->  '
        prompt_3 += os.path.basename(files_new[i])
        prompt_3 += '\n'
    if files_queued == 0:
        prompt_3 += 'Either no files match pattern "%s"\n' % replace_exp
        prompt_3 += 'or you didn\'t change anything \n'
    prompt_3 += '\n'
    prompt_3 += '<Return> -- confirm.\n'
    prompt_3 += '<Escape> -- cancel and exit.\n'

    events_3 = [
        ('ConfirmRename', 'KeyPress-Return'),
    ]
    TkGetUserInput(tk_root, prompt_3, events_3)

    confirm_response = form_data
    if confirm_response:
        RenameFiles(files_old_filtered, files_new_filtered)


if __name__ == '__main__':
    try:
        tk_root = tk.Tk()
        main(tk_root)
    except PermissionError as e:
        ProcessPermissionError(tk_root, e)
    except FileNotFoundError as e:
        ProcessFileNotFoundError(tk_root, e)
    except AssertionError as e:
        ProcessUncaughtException(tk_root, e)
