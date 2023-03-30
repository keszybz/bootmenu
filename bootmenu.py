# SPDX-License-Identifier: LGPL-2.1-or-later

import dataclasses
import enum
import curses
import json
import subprocess
import time

def get_items():
    txt = subprocess.check_output(['bootctl', 'list', '--json=short'],
                                  text=True)
    items = json.loads(txt)
    return items

class MenuState(enum.Enum):
    LIST = 1
    DUMP = 2

@dataclasses.dataclass
class Menu:
    items: list[dict]
    pos: int = 0
    lastkey: str = None
    state: MenuState = None

    def display_list(self, stdscr):
        maxwidth = max(len(item['title']) for item in self.items)
        offset_y = (curses.LINES - len(self.items)) // 2
        offset_x = (curses.COLS - maxwidth) // 2

        for n, item in enumerate(self.items):
            title = item['title']
            stdscr.addstr(offset_y + n,
                          offset_x,
                          f'{title:^{maxwidth}}',
                          curses.A_REVERSE if n == self.pos else 0)

        if self.lastkey:
            stdscr.addstr(curses.LINES - 1, 0, f'{self.lastkey=}')

    def display_dump(self, stdscr, item):
        lines = json.dumps(item, indent=4).split('\n')
        maxwidth = max(len(line) for line in lines)
        maxwidth = min(curses.COLS, maxwidth)

        offset_y = (curses.LINES - len(lines)) // 2
        offset_x = (curses.COLS - maxwidth) // 2
        
        for n, line in enumerate(lines):
            # print(f'{n=} {line=}')

            stdscr.addstr(offset_y + n,
                          offset_x,
                          f'{line:.{maxwidth}}')


    def display(self, stdscr):
        match self.state:
            case MenuState.LIST:
                self.display_list(stdscr)
            case MenuState.DUMP:
                self.display_dump(stdscr, self.items[self.pos])
            case _:
                assert False

    def select(self, stdscr):
        curses.curs_set(False)

        self.state = MenuState.LIST

        while True:
            self.display(stdscr)
            stdscr.refresh()

            key = stdscr.getkey()
            self.lastkey = key
            match key:
                case 'q':
                    break
                case 'KEY_UP':
                    self.pos = max(self.pos - 1, 0)
                case 'KEY_DOWN':
                    self.pos = min(self.pos + 1, len(self.items)-1)
                case 'KEY_LEFT' if self.state != MenuState.LIST:
                    self.state = MenuState.LIST
                case '\n' | 'KEY_RIGHT':
                    self.boot(stdscr, self.items[self.pos])
                case 'd':
                    self.state = MenuState.DUMP
                case _:
                    pass

            stdscr.clear()

    def boot(self, stdscr, item):
        stdscr.clear()
        msg = f"Booting {item['title']}!"
        stdscr.addstr(curses.LINES//2,
                      (curses.COLS - len(msg))//2,
                      msg,
                      curses.A_BOLD)
        stdscr.refresh()
        time.sleep(3)


if __name__ == '__main__':
    items = get_items()
    menu = Menu(items)

    curses.wrapper(menu.select)
