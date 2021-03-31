#   Config
#
#   ----------------------------------------------------------------------
#   Copyright © 2018, 2019, 2020, 2021  Pellegrino Prevete
#
#   All rights reserved
#   ----------------------------------------------------------------------
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from appdirs import user_cache_dir, user_config_dir, user_data_dir
from logging import basicConfig as set_log_config
from logging import INFO as log_level_info
from os.path import join as path_join
from os import makedirs, umask


def mkdirs(newdir, mode=0o700):
    """Because no -p in os.mkdir"""
    original_umask = umask(0)
    try:
        makedirs(newdir, mode)
    except OSError:
        pass
    finally:
        umask(original_umask)


class Config:
    appname = "pgpgram"
    appauthor = "Pellegrino Prevete"

    def __init__(self, 
                 log_level=log_level_info):
        self.setup_logging(log_level)
        self.setup_dirs()

    def get_db_path(self, db_name: str) -> str:
        return path_join(self.get_data_dir(), ".".join([db_name, 'db']))

    def get_cache_dir(self) -> str:
        return user_cache_dir(self.appname, self.appauthor)

    def get_config_dir(self) -> str:
        return user_config_dir(self.appname, self.appauthor)

    def get_data_dir(self) -> str:
        return user_data_dir(self.appname, self.appauthor)

    def setup_dirs(self) -> None:
        mkdirs(self.get_cache_dir())
        mkdirs(self.get_config_dir())
        mkdirs(self.get_data_dir())

    def setup_logging(self, level: int) -> None:
        """Set verbose level"""
        log_config_args = {
            'format': '%(asctime)s %(levelname)-8s %(message)s',
            'level': level,
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
        set_log_config(**log_config_args)
