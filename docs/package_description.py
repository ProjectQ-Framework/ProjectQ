import inspect
import sys
import os


class PackageDescription(object):
    package_list = []

    def __init__(self, name, desc='', module_special_members='__init__',
                 submodule_special_members='', submodules_desc='',
                 helper_submodules=None):
        """
        Args:
            name (str): Name of ProjectQ module
            desc (str): (optional) Description of module
            module_special_members (str): (optional) Special members to include
                in the documentation of the module
            submodule_special_members (str): (optional) Special members to
                include in the documentation of submodules
            submodules_desc (str): (optional) Description to print out before
                the list of submodules
            helper_submodules (list): (optional) List of tuples for helper
                sub-modules to include in the documentation.
                Tuples are (section_title, submodukle_name,
                            automodule_properties)
        """

        self.name = name
        self.desc = desc
        if name not in PackageDescription.package_list:
            PackageDescription.package_list.append(name)

        self.module = sys.modules['projectq.{}'.format(self.name)]
        self.module_special_members = module_special_members

        self.submodule_special_members = module_special_members
        self.submodules_desc = submodules_desc

        self.helper_submodules = helper_submodules

        module_root = os.path.dirname(self.module.__file__)
        sub = [(name, obj) for name, obj in inspect.getmembers(
            self.module,
            lambda obj: inspect.ismodule(obj) and module_root in obj.__file__)
               if name[0] != '_']

        self.subpackages = []
        self.submodules = []
        for name, obj in sub:
            if '{}.{}'.format(self.name,
                              name) in PackageDescription.package_list:
                self.subpackages.append((name, obj))
            else:
                self.submodules.append((name, obj))

        self.subpackages.sort(key=lambda x: x[0].lower())
        self.submodules.sort(key=lambda x: x[0].lower())

        self.members = [(name, obj)
                        for name, obj in inspect.getmembers(
                                self.module,
                                lambda obj: (inspect.isclass(obj)
                                             or inspect.isfunction(obj)
                                             or isinstance(obj, (int,
                                                                 float,
                                                                 tuple,
                                                                 list,
                                                                 dict,
                                                                 set,
                                                                 frozenset,
                                                                 str))))
                        if name[0] != '_']
        self.members.sort(key=lambda x: x[0].lower())

    def get_ReST(self):
        new_lines = []
        new_lines.append(self.name)
        new_lines.append('=' * len(self.name))
        new_lines.append('')

        if self.desc:
            new_lines.append(self.desc.strip())
            new_lines.append('')

        submodule_has_index = False

        if self.subpackages:
            new_lines.append('Subpackages')
            new_lines.append('-' * len(new_lines[-1]))
            new_lines.append('')
            new_lines.append('.. toctree::')
            new_lines.append('    :maxdepth: 1')
            new_lines.append('')
            for name, _ in self.subpackages:
                new_lines.append('    projectq.{}.{}'.format(self.name, name))
            new_lines.append('')
        else:
            submodule_has_index = True
            new_lines.append('.. autosummary::')
            new_lines.append('')
            if self.submodules:
                for name, _ in self.submodules:
                    new_lines.append('\tprojectq.{}.{}'.format(self.name,
                                                               name))
                new_lines.append('')
            if self.members:
                for name, _ in self.members:
                    new_lines.append('\tprojectq.{}.{}'.format(self.name,
                                                               name))
                new_lines.append('')

        if self.submodules:
            new_lines.append('Submodules')
            new_lines.append('-' * len(new_lines[-1]))
            new_lines.append('')
            if self.submodules_desc:
                new_lines.append(self.submodules_desc.strip())
                new_lines.append('')

            if not submodule_has_index:
                new_lines.append('.. autosummary::')
                new_lines.append('')
                for name, _ in self.submodules:
                    new_lines.append('    projectq.{}.{}'.format(self.name,
                                                                 name))
                new_lines.append('')

            for name, _ in self.submodules:
                new_lines.append(name)
                new_lines.append('^' * len(new_lines[-1]))
                new_lines.append('')
                new_lines.append('.. automodule:: projectq.{}.{}'.format(
                    self.name, name))
                new_lines.append('    :members:')
                if self.submodule_special_members:
                    new_lines.append('    :special-members: {}'.format(
                        self.submodule_special_members))
                new_lines.append('    :undoc-members:')
                new_lines.append('')

        new_lines.append('Module contents')
        new_lines.append('-' * len(new_lines[-1]))
        new_lines.append('')
        new_lines.append('.. automodule:: projectq.{}'.format(self.name))
        new_lines.append('    :members:')
        new_lines.append('    :undoc-members:')
        new_lines.append('    :special-members: {}'.format(
            self.module_special_members))
        new_lines.append('    :imported-members:')
        new_lines.append('')

        if self.helper_submodules:
            new_lines.append('Helper sub-modules')
            new_lines.append('-' * len(new_lines[-1]))
            new_lines.append('')
            for title, name, params in self.helper_submodules:
                new_lines.append(title)
                new_lines.append('^' * len(title))
                new_lines.append('')
                new_lines.append('.. automodule:: projectq.{}.{}'.format(
                    self.name, name))
                for param in params:
                    new_lines.append('    {}'.format(param))
                new_lines.append('')

        assert not new_lines[-1]
        return new_lines[:-1]
