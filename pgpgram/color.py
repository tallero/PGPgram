# -*- coding: utf-8 -*-

#    color
#
#    ----------------------------------------------------------------------
#    Copyright © 2018, 2019, 2020, 2021  Pellegrino Prevete
#
#    All rights reserved
#    ----------------------------------------------------------------------
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


class Color:
    BOLD = '\033[1m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    GRAY = '\033[97m'
    END = '\033[0m'

    def set(self, color, text):
        return "{}{}{}{}".format(self.BOLD, color, text, self.END)
