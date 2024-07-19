from generatorapi import generate
import dearpygui.dearpygui as dpg
import pyperclip
import easygui
import sys
import os

w, h = 600, 330

languages = ['English', 'Русский']
default_lang = 'English'

using_custom_charset = False
multiple_gen_path = ''
charset = {'lowerletters': True, 'upperletters': True, 'numbers': True, 'chars': True}  # default charset values
special_charset = {'punctuation': True, 'mathChars': True, 'otherChars': True}
definition_charset = {
    'lowerletters': 'qwertyuiopasdfghjklzxcvbnm', 'upperletters': 'QWERTYUIOPASDFGHJKLZXCVBNM',
    'numbers': '0123456789', 'punctuation': '!?:;.,\"', 'mathChars': '%*+=-/', 'otherChars': '@#$^&()_№|<>'
}
generation_types = {'Basic': False, 'Equally probable': True}

dpg.create_context()
dpg.create_viewport(title='DisisentGen', width=w, height=h)

# cyrillic support
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

big_let_start = 0x00C0  # Capital "A" in cyrillic alphabet
big_let_end = 0x00DF  # Capital "Я" in cyrillic alphabet
small_let_end = 0x00FF  # small "я" in cyrillic alphabet
remap_big_let = 0x0410  # Starting number for remapped cyrillic alphabet
alph_len = big_let_end - big_let_start + 1  # adds the shift from big letters to small
alph_shift = remap_big_let - big_let_start  # adds the shift from remapped to non-remapped
with dpg.font_registry():
    with dpg.font(resource_path("fonts/Roboto-Medium.ttf"), 16) as default_font:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        biglet = remap_big_let  # Starting number for remapped cyrillic alphabet
        for i1 in range(big_let_start, big_let_end + 1):  # Cycle through big letters in cyrillic alphabet
            dpg.add_char_remap(i1, biglet)  # Remap the big cyrillic letter
            dpg.add_char_remap(i1 + alph_len, biglet + alph_len)  # Remap the small cyrillic letter
            biglet += 1  # choose next letter
        dpg.bind_font(default_font)


def _help(message):
    last_item = dpg.last_item()
    group = dpg.add_group(horizontal=True)
    dpg.move_item(last_item, parent=group)
    dpg.capture_next_item(lambda s: dpg.move_item(s, parent=group))
    t = dpg.add_text("(?)", color=[0, 255, 0])
    with dpg.tooltip(t):
        dpg.add_text(message)


def _toggle_show_callback():
    toggle_show_password(not dpg.is_item_visible('password_showed'))


def toggle_show_password(show):
    if show:  # show
        dpg.hide_item('password')
        dpg.show_item('password_showed')
        dpg.set_item_label('toggle_show', 'Hide')
    else:  # hide
        dpg.hide_item('password_showed')
        dpg.show_item('password')
        dpg.set_item_label('toggle_show', 'Show')


def _copy_password():
    pyperclip.copy(dpg.get_value('password'))


def _switch_charset(charset_type, new_bool):
    charset[charset_type] = new_bool

    if charset_type == 'chars':
        for i in special_charset:
            dpg.set_value(i, new_bool)
            special_charset[i] = new_bool
            dpg.enable_item(i) if new_bool else dpg.disable_item(i)

    _update_custom_charset(charset_type, new_bool)
    _update_using_custom_charset()


def _switch_special_charset(charset_type, new_bool):
    special_charset[charset_type] = new_bool
    _update_custom_charset(charset_type, new_bool)
    _update_using_custom_charset()


def _update_custom_charset(charset_type='letters', new_bool=True):
    all_charset = ''

    if not using_custom_charset:
        for i in charset:
            if i == 'chars': continue
            if charset[i]:
                all_charset += definition_charset[i]

        for i in special_charset:
            if special_charset[i]:
                all_charset += definition_charset[i]
    else:
        all_charset = dpg.get_value('custom_charset')

        if new_bool:
            all_charset += definition_charset[charset_type]
        else:
            all_charset = all_charset.replace(definition_charset[charset_type], '')

    dpg.set_value('custom_charset', all_charset)
    _filter_custom_charset()


def _select_folder():
    path = easygui.diropenbox()
    global multiple_gen_path
    multiple_gen_path = path
    dpg.set_item_label('select_folder', path)


def _multiple_gen_callback():
    if multiple_gen_path == '': return

    dpg.hide_item('multiplegenerate_modal')

    generated = generate(
        length=dpg.get_value('length'),
        numbers=charset['numbers'],
        lower_letters=charset['lowerletters'],
        upper_letters=charset['upperletters'],
        schars=charset['chars'],
        user_chars=dpg.get_value('custom_charset') if using_custom_charset else '',
        template=dpg.get_value('formatting_str') if dpg.get_value('formatting_enable') else '',
        default_template_key=dpg.get_value('formatting_letter') if dpg.get_value('formatting_enable') else '',
        equal_count=generation_types[dpg.get_value('generation_type')],
        count=dpg.get_value('count'),
    )

    with open(multiple_gen_path + '\\generated-passwords.txt', 'w') as file:
        file.write('\n'.join(generated))


def _generate_callback():
    generated = generate(
        length=dpg.get_value('length'),
        numbers=charset['numbers'],
        lower_letters=charset['lowerletters'],
        upper_letters=charset['upperletters'],
        schars=charset['chars'],
        user_chars=dpg.get_value('custom_charset') if using_custom_charset else '',
        template=dpg.get_value('formatting_str') if dpg.get_value('formatting_enable') else '',
        default_template_key=dpg.get_value('formatting_letter') if dpg.get_value('formatting_enable') else '',
        equal_count=generation_types[dpg.get_value('generation_type')],
    )

    dpg.set_value('password', generated)


def _filter_custom_charset():  # костыль из-за https://github.com/hoffstadt/DearPyGui/issues/643
    new_str = dpg.get_value('custom_charset')
    stripped = "".join(dict.fromkeys(new_str))
    if stripped != new_str:
        dpg.set_value('custom_charset', stripped)
        return


with dpg.item_handler_registry(tag='custom_charset_handler') as handler:
    dpg.add_item_deactivated_after_edit_handler(callback=_filter_custom_charset)


def _custom_charset_callback():
    _update_using_custom_charset(True)


def _update_using_custom_charset(from_callback=False):
    global using_custom_charset
    using_custom_charset = False

    for group_chars in definition_charset:  # update checkboxes if manually removed/added their chars
        if charset['chars'] and (group_chars in special_charset) and (not special_charset[group_chars]):
            using_custom_charset = True
            if not from_callback: break

        before_not_found_char = False
        found_char = False
        for char in definition_charset[group_chars]:  # check each char, because don't care about permutation
            if dpg.get_value('custom_charset').find(char) == -1:
                if from_callback:
                    dpg.set_value(group_chars, False)
                    if group_chars in charset: charset[group_chars] = False
                    if group_chars in special_charset: special_charset[group_chars] = False

                if found_char:
                    using_custom_charset = True
                    break
                before_not_found_char = True
            else:
                if before_not_found_char:
                    using_custom_charset = True
                    break
                found_char = True
        else:
            if from_callback:
                dpg.set_value(group_chars, True)
                if group_chars in charset: charset[group_chars] = True
                if group_chars in special_charset: special_charset[group_chars] = True

with dpg.window(label='DisisentGen', tag='main'):
    with dpg.group(horizontal=True):
        dpg.add_input_text(tag='password', label="Password", hint='Generated password will be here', password=True)
        dpg.add_input_text(tag='password_showed', label="Password", hint='Generated password will be here',
                           source='password', show=False)
        # lang = dpg.add_combo(items=['English', 'Русский'], default_value=default_lang, width=115)

    with dpg.group(horizontal=True):
        dpg.add_slider_int(tag='length', label='Length', default_value=32, min_value=1, max_value=128)
        _help('Ctrl + LMB to manual edit')

    with dpg.group(horizontal=True):
        dpg.add_button(label='Generate', callback=_generate_callback)

        dpg.add_button(label="Multiple Generate")
        with dpg.popup(dpg.last_item(), modal=True, mousebutton=dpg.mvMouseButton_Left, tag="multiplegenerate_modal"):
            dpg.add_text('You need to select the folder where the file will be created generated-passwords.txt')
            dpg.add_button(tag='select_folder', label="Select folder", callback=_select_folder)
            dpg.add_spacer()
            dpg.add_slider_int(tag='count', label='Count', min_value=1, max_value=1024, default_value=1)
            _help('Ctrl + LMB to manual edit')
            dpg.add_spacer()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Generate", width=75, callback=_multiple_gen_callback)
                dpg.add_button(label="Cancel", width=75,
                               callback=lambda: dpg.hide_item('multiplegenerate_modal'))

        dpg.add_button(tag='toggle_show', label='Show', callback=_toggle_show_callback)
        dpg.add_button(tag='copy', label='Copy', callback=_copy_password)

    with dpg.group(horizontal=True):
        dpg.add_checkbox(tag='lowerletters', label='Lower letters', default_value=charset['lowerletters'],
                         callback=_switch_charset)
        dpg.add_checkbox(tag='upperletters', label='Upper letters', default_value=charset['upperletters'],
                         callback=_switch_charset)
        dpg.add_checkbox(tag='numbers', label='Numbers', default_value=charset['numbers'], callback=_switch_charset)
        dpg.add_checkbox(tag='chars', label='Special characters', default_value=charset['chars'],
                         callback=_switch_charset)

    with dpg.collapsing_header(label="Extra settings"):
        with dpg.group(horizontal=True):
            dpg.add_checkbox(tag='punctuation', label="!?:;.,\"", default_value=special_charset['punctuation'],
                             callback=_switch_special_charset)
            dpg.add_checkbox(tag='mathChars', label="%*+=-/", default_value=special_charset['mathChars'],
                             callback=_switch_special_charset)
            dpg.add_checkbox(tag='otherChars', label="@#$^&()_№|<>", default_value=special_charset['otherChars'],
                             callback=_switch_special_charset)

        dpg.add_input_text(tag='custom_charset', label='Custom charset',
                           hint='Enter a charset or use the checkboxes',
                           no_spaces=True, callback=_custom_charset_callback)
        dpg.bind_item_handler_registry('custom_charset', "custom_charset_handler")

        dpg.add_spacer()
        dpg.add_combo(tag='generation_type', items=[i for i in generation_types.keys()], label='Generation types', width=150, default_value='Basic')

        dpg.add_spacer()
        dpg.add_text(default_value='Formatting')
        with dpg.group(horizontal=True):
            dpg.add_checkbox(tag='formatting_enable')
            dpg.add_input_text(tag='formatting_str', default_value='XXXX-XXXX')
            dpg.add_input_text(tag='formatting_letter', default_value='X', no_spaces=True, width=17)
            _help('Checkbox: To enable formatting, this disable length parameter\n'
                  'Center input: Your formatting string\n'
                  'Last box: The letter that needs to be replaced')

_update_custom_charset()

dpg.set_primary_window('main', True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
