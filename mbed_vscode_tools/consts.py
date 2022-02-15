import platform


TOOL_CONFFILE_NAME = '.mbed-vscode-tools.json'
TOOL_CONFFILE_INDENT_LENGTH = 4
CMAKE_ROOTDIR_NAME = 'cmake_build'
CMAKE_CONFFILE_NAME = 'mbed_config.cmake'
NINJA_BUILDFILE_NAME = 'build.ninja'
VSCODE_CONFFILE_NAME = 'c_cpp_properties.json'
VSCODE_CONFFILE_INDENT_LENGTH = 4
VSCODE_CONFENTRY_BASE = 'Mbed'

# Identify os type
_os_type = platform.system()
if _os_type == 'Darwin':
    VSCODE_CONFENTRY_AUTO = 'Mac'
elif _os_type == 'Windows':
    VSCODE_CONFENTRY_AUTO = 'Win32'
elif _os_type == 'Linux':
    VSCODE_CONFENTRY_AUTO = 'Linux'
else:
    raise Exception(f'Unexpected platform ({_os_type}) detected.')
