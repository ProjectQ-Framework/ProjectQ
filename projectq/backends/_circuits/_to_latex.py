#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import json
from projectq.ops import Measure, Allocate, Deallocate, X, Z, Swap


def to_latex(circuit):
    """
    Translates a given circuit to a TikZ picture in a Latex document.

    It uses a json-configuration file which (if it does not exist) is created
    automatically upon running this function for the first time. The config
    file can be used to determine custom gate sizes, offsets, etc.

    New gate options can be added under settings['gates'], using the gate
    class name string as a key. Every gate can have its own width, height, pre
    offset and offset.

    Example:
        .. code-block:: python

            settings['gates']['HGate'] = {'width': .5, 'offset': .15}

    The default settings can be acquired using the get_default_settings()
    function, and written using write_settings().

    Args:
        circuit (list<list<CircuitItem>>): Each qubit line is a list of
            CircuitItem objects, i.e., in circuit[line].

    Returns:
        tex_doc_str (string): Latex document string which can be compiled
            using, e.g., pdflatex.
    """
    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError  # for Python2 compatibility

    try:
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
    except FileNotFoundError:
        settings = write_settings(get_default_settings())

    text = _header(settings)
    text += _body(circuit, settings)
    text += _footer(settings)
    return text


def write_settings(settings):
    """
    Write all settings to a json-file.

    Args:
        settings (dict): Settings dict to write.
    """
    with open('settings.json', 'w') as settings_file:
        json.dump(settings, settings_file, sort_keys=True, indent=4)
    return settings


def get_default_settings():
    """
    Return the default settings for the circuit drawing function to_latex().

    Returns:
        settings (dict): Default circuit settings
    """
    settings = dict()
    settings['gate_shadow'] = True
    settings['lines'] = ({'style': 'very thin', 'double_classical': True,
                          'init_quantum': True, 'double_lines_sep': .04})
    settings['gates'] = ({'HGate': {'width': .5, 'offset': .3,
                                    'pre_offset': .1},
                          'XGate': {'width': .35, 'height': .35,
                                    'offset': .1},
                          'SwapGate': {'width': .35, 'height': .35,
                                       'offset': .1},
                          'Rx': {'width': 1., 'height': .8, 'pre_offset': .2,
                                 'offset': .3},
                          'Ry': {'width': 1., 'height': .8, 'pre_offset': .2,
                                 'offset': .3},
                          'Rz': {'width': 1., 'height': .8, 'pre_offset': .2,
                                 'offset': .3},
                          'EntangleGate': {'width': 1.8, 'offset': .2,
                                           'pre_offset': .2},
                          'DeallocateQubitGate': {'height': .15, 'offset': .2,
                                                  'width': .2,
                                                  'pre_offset': .1},
                          'AllocateQubitGate': {'height': .15, 'width': .2,
                                                'offset': .1,
                                                'pre_offset': .1,
                                                'draw_id': False},
                          'MeasureGate': {'width': 0.75, 'offset': .2,
                                          'height': .5, 'pre_offset': .2}
                          })
    settings['control'] = {'size': .1, 'shadow': False}
    return settings


def _header(settings):
    """
    Writes the Latex header using the settings file.

    The header includes all packages and defines all tikz styles.

    Returns:
        header (string): Header of the Latex document.
    """
    packages = ("\\documentclass{standalone}\n\\usepackage[margin=1in]"
                "{geometry}\n\\usepackage[hang,small,bf]{caption}\n"
                "\\usepackage{tikz}\n"
                "\\usepackage{braket}\n\\usetikzlibrary{backgrounds,shadows."
                "blur,fit,decorations.pathreplacing,shapes}\n\n")

    init = ("\\begin{document}\n"
            "\\begin{tikzpicture}[scale=0.8, transform shape]\n\n")

    gate_style = ("\\tikzstyle{basicshadow}=[blur shadow={shadow blur steps=8,"
                  " shadow xshift=0.7pt, shadow yshift=-0.7pt, shadow scale="
                  "1.02}]")

    if not (settings['gate_shadow'] or settings['control']['shadow']):
        gate_style = ""

    gate_style += "\\tikzstyle{basic}=[draw,fill=white,"
    if settings['gate_shadow']:
        gate_style += "basicshadow"
    gate_style += "]\n"

    gate_style += ("\\tikzstyle{operator}=[basic,minimum size=1.5em]\n"
                   "\\tikzstyle{phase}=[fill=black,shape=circle," +
                   "minimum size={}".format(settings['control']['size'])
                   + "cm,inner sep=0pt,outer sep=0pt,draw=black"
                   )
    if settings['control']['shadow']:
        gate_style += ",basicshadow"
    gate_style += ("]\n\\tikzstyle{none}=[inner sep=0pt,outer sep=-.5pt,"
                   "minimum height=0.5cm+1pt]\n"
                   "\\tikzstyle{measure}=[operator,inner sep=0pt,minimum "
                   + "height={}cm, minimum width={}cm]\n".format(
                       settings['gates']['MeasureGate']['height'],
                       settings['gates']['MeasureGate']['width']) +
                   "\\tikzstyle{xstyle}=[circle,basic,minimum height=")
    x_gate_radius = min(settings['gates']['XGate']['height'],
                        settings['gates']['XGate']['width'])
    gate_style += ("{x_rad}cm,minimum width={x_rad}cm,inner sep=0pt,"
                   "{linestyle}]\n"
                   ).format(x_rad=x_gate_radius,
                            linestyle=settings['lines']['style'])
    if settings['gate_shadow']:
        gate_style += ("\\tikzset{\nshadowed/.style={preaction={transform "
                       "canvas={shift={(0.5pt,-0.5pt)}}, draw=gray, opacity="
                       "0.4}},\n}\n")
    gate_style += "\\tikzstyle{swapstyle}=["
    gate_style += "inner sep=-1pt, outer sep=-1pt, minimum width=0pt]\n"
    edge_style = ("\\tikzstyle{edgestyle}=[" + settings['lines']['style'] +
                  "]\n")

    return packages + init + gate_style + edge_style


def _body(circuit, settings):
    """
    Return the body of the Latex document, including the entire circuit in
    TikZ format.

    Args:
        circuit (list<list<CircuitItem>>): Circuit to draw.

    Returns:
        tex_str (string): Latex string to draw the entire circuit.
    """
    code = []

    conv = _Circ2Tikz(settings, len(circuit))
    for line in range(len(circuit)):
        code.append(conv.to_tikz(line, circuit))

    return "".join(code)


def _footer(settings):
    """
    Return the footer of the Latex document.

    Returns:
        tex_footer_str (string): Latex document footer.
    """
    return "\n\n\end{tikzpicture}\n\end{document}"


class _Circ2Tikz(object):
    """
    The Circ2Tikz class takes a circuit (list of lists of CircuitItem objects)
    and turns them into Latex/TikZ code.

    It uses the settings dictionary for gate offsets, sizes, spacing, ...
    """
    def __init__(self, settings, num_lines):
        """
        Initialize a circuit to latex converter object.

        Args:
            settings (dict): Dictionary of settings to use for the TikZ image.
            num_lines (int): Number of qubit lines to use for the entire
                circuit.
        """
        self.settings = settings
        self.pos = [0.] * num_lines
        self.op_count = [0] * num_lines
        self.is_quantum = [settings['lines']['init_quantum']] * num_lines

    def to_tikz(self, line, circuit, end=None):
        """
        Generate the TikZ code for one line of the circuit up to a certain
        gate.

        It modifies the circuit to include only the gates which have not been
        drawn. It automatically switches to other lines if the gates on those
        lines have to be drawn earlier.

        Args:
            line (int): Line to generate the TikZ code for.
            circuit (list<list<CircuitItem>>): The circuit to draw.
            end (int): Gate index to stop at (for recursion).

        Returns:
            tikz_code (string): TikZ code representing the current qubit line
                and, if it was necessary to draw other lines, those lines as
                well.
        """
        if end is None:
            end = len(circuit[line])

        tikz_code = []

        cmds = circuit[line]
        for i in range(0, end):
            gate = cmds[i].gate
            lines = cmds[i].lines
            ctrl_lines = cmds[i].ctrl_lines

            all_lines = lines + ctrl_lines
            all_lines.remove(line)  # remove current line
            for l in all_lines:
                gate_idx = 0
                while not (circuit[l][gate_idx] == cmds[i]):
                    gate_idx += 1

                tikz_code.append(self.to_tikz(l, circuit, gate_idx))
                # we are taking care of gate 0 (the current one)
                circuit[l] = circuit[l][1:]

            all_lines = lines + ctrl_lines
            pos = max([self.pos[l] for l in range(min(all_lines),
                                                  max(all_lines)+1)])
            for l in range(min(all_lines), max(all_lines)+1):
                self.pos[l] = pos + self._gate_pre_offset(gate)

            connections = ""
            for l in all_lines:
                connections += self._line(self.op_count[l] - 1,
                                          self.op_count[l], line=l)
            add_str = ""
            if gate == X:
                # draw NOT-gate with controls
                add_str = self._x_gate(lines, ctrl_lines)
                # and make the target qubit quantum if one of the controls is
                if not self.is_quantum[lines[0]]:
                    if sum([self.is_quantum[i] for i in ctrl_lines]) > 0:
                        self.is_quantum[lines[0]] = True
            elif gate == Z and len(ctrl_lines) > 0:
                add_str = self._cz_gate(lines + ctrl_lines)
            elif gate == Swap:
                add_str = self._swap_gate(lines, ctrl_lines)
            elif gate == Measure:
                # draw measurement gate
                for l in lines:
                    op = self._op(l)
                    width = self._gate_width(Measure)
                    height = self._gate_height(Measure)
                    shift0 = .07 * height
                    shift1 = .36 * height
                    shift2 = .1 * width
                    add_str += ("\n\\node[measure,edgestyle] ({op}) at ({pos}"
                                ",-{line}) {{}};\n\\draw[edgestyle] ([yshift="
                                "-{shift1}cm,xshift={shift2}cm]{op}.west) to "
                                "[out=60,in=180] ([yshift={shift0}cm]{op}."
                                "center) to [out=0, in=120] ([yshift=-{shift1}"
                                "cm,xshift=-{shift2}cm]{op}.east);\n"
                                "\\draw[edgestyle] ([yshift=-{shift1}cm]{op}."
                                "center) to ([yshift=-{shift2}cm,xshift=-"
                                "{shift1}cm]{op}.north east);"
                                ).format(op=op, pos=self.pos[l], line=l,
                                         shift0=shift0, shift1=shift1,
                                         shift2=shift2)
                    self.op_count[l] += 1
                    self.pos[l] += (self._gate_width(gate) +
                                    self._gate_offset(gate))
                    self.is_quantum[l] = False
            elif gate == Allocate:
                # draw 'begin line'
                add_str = "\n\\node[none] ({}) at ({},-{}) {{$\Ket{{0}}{}$}};"
                id_str = ""
                if self.settings['gates']['AllocateQubitGate']['draw_id']:
                    id_str = "^{{\\textcolor{{red}}{{{}}}}}".format(cmds[i].id)
                add_str = add_str.format(self._op(line), self.pos[line], line,
                                         id_str)
                self.op_count[line] += 1
                self.pos[line] += (self._gate_offset(gate) +
                                   self._gate_width(gate))
                self.is_quantum[line] = self.settings['lines']['init_quantum']
            elif gate == Deallocate:
                # draw 'end of line'
                op = self._op(line)
                add_str = "\n\\node[none] ({}) at ({},-{}) {{}};"
                add_str = add_str.format(op, self.pos[line], line)
                yshift = str(self._gate_height(gate)) + "cm]"
                add_str += ("\n\\draw ([yshift={yshift}{op}.center) edge "
                            "[edgestyle] ([yshift=-{yshift}{op}.center);"
                            ).format(op=op, yshift=yshift)
                self.op_count[line] += 1
                self.pos[line] += (self._gate_width(gate) +
                                   self._gate_offset(gate))
            else:
                # regular gate must draw the lines it does not act upon
                # if it spans multiple qubits
                add_str = self._regular_gate(gate, lines, ctrl_lines)
                for l in lines:
                    self.is_quantum[l] = True

            tikz_code.append(add_str)
            if not gate == Allocate:
                tikz_code.append(connections)

        circuit[line] = circuit[line][end:]
        return "".join(tikz_code)

    def _gate_name(self, gate):
        """
        Return the string representation of the gate.

        Tries to use gate.tex_str and, if that is not available, uses str(gate)
        instead.

        Args:
            gate: Gate object of which to get the name / latex representation.

        Returns:
            gate_name (string): Latex gate name.
        """
        try:
            name = gate.tex_str()
        except AttributeError:
            name = str(gate)
        return name

    def _swap_gate(self, lines, ctrl_lines):
        """
        Return the TikZ code for a Swap-gate.

        Args:
            lines (list<int>): List of length 2 denoting the target qubit of
                the Swap gate.
            ctrl_lines (list<int>): List of qubit lines which act as controls.

        """
        assert(len(lines) == 2)  # NOT gate only acts on 1 qubit
        delta_pos = self._gate_offset(Swap)
        gate_width = self._gate_width(Swap)
        lines.sort()

        gate_str = ""
        for line in lines:
            op = self._op(line)
            w = "{}cm".format(.5*gate_width)
            s1 = "[xshift=-{w},yshift=-{w}]{op}.center".format(w=w, op=op)
            s2 = "[xshift={w},yshift={w}]{op}.center".format(w=w, op=op)
            s3 = "[xshift=-{w},yshift={w}]{op}.center".format(w=w, op=op)
            s4 = "[xshift={w},yshift=-{w}]{op}.center".format(w=w, op=op)
            swap_style = "swapstyle,edgestyle"
            if self.settings['gate_shadow']:
                swap_style += ",shadowed"
            gate_str += ("\n\\node[swapstyle] ({op}) at ({pos},-{line}) {{}};"
                         "\n\\draw[{swap_style}] ({s1})--({s2});\n"
                         "\\draw[{swap_style}] ({s3})--({s4});"
                         ).format(op=op, s1=s1, s2=s2, s3=s3, s4=s4,
                                  line=line, pos=self.pos[line],
                                  swap_style=swap_style)
        gate_str += self._line(lines[0], lines[1])

        if len(ctrl_lines) > 0:
            for ctrl in ctrl_lines:
                gate_str += self._phase(ctrl, self.pos[lines[0]])
                if ctrl > lines[1] or ctrl < lines[0]:
                    closer_line = lines[0]
                    if ctrl > lines[1]:
                        closer_line = lines[1]
                    gate_str += self._line(ctrl, closer_line)

        all_lines = ctrl_lines + lines
        new_pos = self.pos[lines[0]] + delta_pos + gate_width
        for i in all_lines:
            self.op_count[i] += 1
        for i in range(min(all_lines), max(all_lines)+1):
            self.pos[i] = new_pos
        return gate_str

    def _x_gate(self, lines, ctrl_lines):
        """
        Return the TikZ code for a NOT-gate.

        Args:
            lines (list<int>): List of length 1 denoting the target qubit of
                the NOT / X gate.
            ctrl_lines (list<int>): List of qubit lines which act as controls.

        """
        assert(len(lines) == 1)  # NOT gate only acts on 1 qubit
        line = lines[0]
        delta_pos = self._gate_offset(X)
        gate_width = self._gate_width(X)
        op = self._op(line)
        gate_str = ("\n\\node[xstyle] ({op}) at ({pos},-{line}) {{}};\n\\draw"
                    "[edgestyle] ({op}.north)--({op}.south);\n\\draw"
                    "[edgestyle] ({op}.west)--({op}.east);"
                    ).format(op=op, line=line, pos=self.pos[line])

        if len(ctrl_lines) > 0:
            for ctrl in ctrl_lines:
                gate_str += self._phase(ctrl, self.pos[line])
                gate_str += self._line(ctrl, line)

        all_lines = ctrl_lines + [line]
        new_pos = self.pos[line] + delta_pos + gate_width
        for i in all_lines:
            self.op_count[i] += 1
        for i in range(min(all_lines), max(all_lines)+1):
            self.pos[i] = new_pos
        return gate_str

    def _cz_gate(self, lines):
        """
        Return the TikZ code for an n-controlled Z-gate.

        Args:
            lines (list<int>): List of all qubits involved.
        """
        assert len(lines) > 1
        line = lines[0]
        delta_pos = self._gate_offset(Z)
        gate_width = self._gate_width(Z)
        gate_str = self._phase(line, self.pos[line])

        for ctrl in lines[1:]:
            gate_str += self._phase(ctrl, self.pos[line])
            gate_str += self._line(ctrl, line)

        new_pos = self.pos[line] + delta_pos + gate_width
        for i in lines:
            self.op_count[i] += 1
        for i in range(min(lines), max(lines)+1):
            self.pos[i] = new_pos
        return gate_str

    def _gate_width(self, gate):
        """
        Return the gate width, using the settings (if available).

        Returns:
            gate_width (float): Width of the gate.
                (settings['gates'][gate_class_name]['width'])
        """
        try:
            gates = self.settings['gates']
            gate_width = gates[gate.__class__.__name__]['width']
        except KeyError:
            gate_width = .5
        return gate_width

    def _gate_pre_offset(self, gate):
        """
        Return the offset to use before placing this gate.

        Returns:
            gate_pre_offset (float): Offset to use before the gate.
                (settings['gates'][gate_class_name]['pre_offset'])
        """
        try:
            gates = self.settings['gates']
            delta_pos = gates[gate.__class__.__name__]['pre_offset']
        except KeyError:
            delta_pos = self._gate_offset(gate)
        return delta_pos

    def _gate_offset(self, gate):
        """
        Return the offset to use after placing this gate and, if no pre_offset
        is defined, the same offset is used in front of the gate.

        Returns:
            gate_offset (float): Offset.
                (settings['gates'][gate_class_name]['offset'])
        """
        try:
            gates = self.settings['gates']
            delta_pos = gates[gate.__class__.__name__]['offset']
        except KeyError:
            delta_pos = .2
        return delta_pos

    def _gate_height(self, gate):
        """
        Return the height to use for this gate.

        Returns:
            gate_height (float): Height of the gate.
                (settings['gates'][gate_class_name]['height'])
        """
        try:
            height = self.settings['gates'][gate.__class__.__name__]['height']
        except KeyError:
            height = .5
        return height

    def _phase(self, line, pos):
        """
        Places a phase / control circle on a qubit line at a given position.

        Args:
            line (int): Qubit line at which to place the circle.
            pos (float): Position at which to place the circle.

        Returns:
            tex_str (string): Latex string representing a control circle at the
                given position.
        """
        phase_str = "\n\\node[phase] ({}) at ({},-{}) {{}};"
        return phase_str.format(self._op(line), pos, line)

    def _op(self, line, op=None, offset=0):
        """
        Returns the gate name for placing a gate on a line.

        Args:
            line (int): Line number.
            op (int): Operation number or, by default, uses the current op
                count.

        Returns:
            op_str (string): Gate name.
        """
        if op is None:
            op = self.op_count[line]
        return "line{}_gate{}".format(line, op + offset)

    def _line(self, p1, p2, double=False, line=None):
        """
        Connects p1 and p2, where p1 and p2 are either to qubit line indices,
        in which case the two most recent gates are connected, or two gate
        indices, in which case line denotes the line number and the two gates
        are connected on the given line.

        Args:
            p1 (int): Index of the first object to connect.
            p2 (int): Index of the second object to connect.
            double (bool): Draws double lines if True.
            line (int or None): Line index - if provided, p1 and p2 are gate
                indices.

        Returns:
            tex_str (string): Latex code to draw this / these line(s).
        """
        dbl_classical = self.settings['lines']['double_classical']

        if line is None:
            quantum = not dbl_classical or self.is_quantum[p1]
            op1, op2 = self._op(p1), self._op(p2)
            loc1, loc2 = 'north', 'south'
            shift = "xshift={}cm"
        else:
            quantum = not dbl_classical or self.is_quantum[line]
            op1, op2 = self._op(line, p1), self._op(line, p2)
            loc1, loc2 = 'west', 'east'
            shift = "yshift={}cm"

        if quantum:
            return "\n\\draw ({}) edge[edgestyle] ({});".format(op1, op2)
        else:
            if p2 > p1:
                loc1, loc2 = loc2, loc1
            edge_str = ("\n\\draw ([{shift}]{op1}.{loc1}) edge[edgestyle] "
                        "([{shift}]{op2}.{loc2});")
            line_sep = self.settings['lines']['double_lines_sep']
            shift1 = shift.format(line_sep / 2.)
            shift2 = shift.format(-line_sep / 2.)
            edges_str = edge_str.format(shift=shift1, op1=op1, op2=op2,
                                        loc1=loc1, loc2=loc2)
            edges_str += edge_str.format(shift=shift2, op1=op1, op2=op2,
                                         loc1=loc1, loc2=loc2)
            return edges_str

    def _regular_gate(self, gate, lines, ctrl_lines):
        """
        Draw a regular gate.

        Args:
            gate: Gate to draw.
            lines (list<int>): Lines the gate acts on.
            ctrl_lines (list<int>): Control lines.

        Returns:
            tex_str (string): Latex string drawing a regular gate at the given
                location
        """
        imax = max(lines)
        imin = min(lines)

        gate_lines = lines + ctrl_lines

        delta_pos = self._gate_offset(gate)
        gate_width = self._gate_width(gate)
        gate_height = self._gate_height(gate)

        name = self._gate_name(gate)

        lines = list(range(imin, imax+1))

        tex_str = ""
        pos = self.pos[lines[0]]

        node_str = "\n\\node[none] ({}) at ({},-{}) {{}};"
        for l in lines:
            node1 = node_str.format(self._op(l), pos, l)
            node2 = ("\n\\node[none,minimum height={}cm,outer sep=0] ({}) at"
                     " ({},-{}) {{}};"
                     ).format(gate_height, self._op(l, offset=1),
                              pos + gate_width/2., l)
            node3 = node_str.format(self._op(l, offset=2),
                                    pos + gate_width, l)
            tex_str += node1 + node2 + node3
            if not l in gate_lines:
                tex_str += self._line(self.op_count[l] - 1, self.op_count[l],
                                      line=l)

        tex_str += ("\n\\draw[operator,edgestyle,outer sep={width}cm] (["
                    "yshift={half_height}cm]{op1}) rectangle ([yshift=-"
                    "{half_height}cm]{op2}) node[pos=.5] {{{name}}};"
                    ).format(width=gate_width, op1=self._op(imin),
                             op2=self._op(imax, offset=2),
                             half_height=.5 * gate_height,
                             name=name)

        for l in lines:
            self.pos[l] = pos + gate_width/2.
            self.op_count[l] += 1

        for ctrl in ctrl_lines:
            if not ctrl in lines:
                tex_str += self._phase(ctrl, pos + gate_width/2.)
                connect_to = imax
                if abs(connect_to - ctrl) > abs(imin - ctrl):
                    connect_to = imin
                tex_str += self._line(ctrl, connect_to)
                self.pos[ctrl] = pos + delta_pos + gate_width
                self.op_count[ctrl] += 1

        for l in lines:
            self.op_count[l] += 2

        for l in range(min(ctrl_lines + lines), max(ctrl_lines + lines)+1):
            self.pos[l] = pos + delta_pos + gate_width
        return tex_str
