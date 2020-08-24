import numpy as np

from meshio._mesh import Mesh


def debugger(line, content):
    debugger1 = content[line - 1]
    debugger2 = content[line]
    debugger3 = content[line + 1]

    return debugger1, debugger2, debugger3


def _read_commented_int(line, content):
    d1, d2, d3 = debugger(line, content)
    return int(content[line].split("#")[0])


def read_array(line, content, n_nod, dim, dtype):
    points = np.zeros([n_nod, dim], dtype=dtype)
    for array_line in range(n_nod):
        d1, d2, d3 = debugger(line + array_line, content)
        hej = content[line + array_line].split()
        points[array_line, :] = hej

    line += array_line

    return points, line


class ComsolMeshIO:
    format = "comsol"

    def read_txt(self, filename, **kwargs):

        # self.fd = fd = open(self.filename, "r")
        with open(filename, "r") as f:
            content = f.readlines()

        mode = "header"

        # coors = conns = None
        line = 0
        while 1:
            if mode == "header":
                line += 4

                # n_tags = content[line]
                n_tags = _read_commented_int(line, content)
                line += 2
                for i in range(n_tags):
                    line += 1
                n_types = _read_commented_int(line, content)
                for i in range(n_types):
                    line += 1

                line += 6
                assert content[line].split()[1] == "Mesh"
                line += 2
                dim = _read_commented_int(line, content)
                assert (dim == 2) or (dim == 3)
                line += 1
                n_nod = _read_commented_int(line, content)
                line += 1
                i0 = _read_commented_int(line, content)
                mode = "points"

            elif mode == "points":
                line += 3
                coors, line = read_array(line, content, n_nod, dim, "float64")
                mesh = Mesh(coors, {})
                mode = "cells"

            elif mode == "cells":
                line += 2
                n_types = _read_commented_int(line, content)
                conns = []
                descs = []
                mat_ids = []
                line += 4

                for it in range(n_types):
                    d1, d2, d3 = debugger(line, content)
                    t_name = content[line].split()[1]
                    line += 3
                    n_ep = _read_commented_int(line, content)
                    line += 1
                    n_el = _read_commented_int(line, content)
                    line += 2

                    aux, line = read_array(line, content, n_el, n_ep, "int32")
                    if t_name == "tri":
                        conns.append(aux)
                        descs.append("2_3")
                        is_conn = True
                    elif t_name == "quad":
                        # Rearrange element node order to match SfePy.
                        aux = aux[:, (0, 1, 3, 2)]
                        conns.append(aux)
                        descs.append("2_4")
                        is_conn = True
                    elif t_name == "hex":
                        # Rearrange element node order to match SfePy.
                        aux = aux[:, (0, 1, 3, 2, 4, 5, 7, 6)]
                        conns.append(aux)
                        descs.append("3_8")
                        is_conn = True
                    elif t_name == "tet":
                        conns.append(aux)
                        descs.append("3_4")
                        is_conn = True
                    else:
                        is_conn = False

                    # Skip parameters.
                    line += 2
                    n_pv = _read_commented_int(line, content)
                    n_par = _read_commented_int(line, content)
                    # for ii in range(n_par):
                    line += n_par + 5

                    # d1, d2, d3 = debugger(line, content)
                    # n_domain = _read_commented_int(line, content)
                    # assert_(n_domain == n_el)
                    # if is_conn:
                    #     self._skip_comment()
                    #     mat_id = read_array(fd, n_domain, 1, nm.int32)
                    #     mat_ids.append(mat_id.squeeze())
                    # else:
                    #     for ii in range(n_domain):
                    #         skip_read_line(fd)

                    # Skip up/down pairs.
                    # n_ud = self._read_commented_int()
                    # for ii in range(n_ud):
                    #     skip_read_line(fd)

                    mesh.cells[t_name] = aux
                break

        # mesh._set_io_data(coors, None, conns, mat_ids, descs)

        return mesh

    def write(self, filename, mesh, out=None, **kwargs):
        def write_elements(
            fd, ig, conn, mat_ids, type_name, npe, format, norder, nm_params
        ):
            fd.write("# Type #%d\n\n" % ig)
            fd.write("%s # type name\n\n\n" % type_name)
            fd.write("%d # number of nodes per element\n" % npe)
            fd.write("%d # number of elements\n" % conn.shape[0])
            fd.write("# Elements\n")
            for ii in range(conn.shape[0]):
                nn = conn[ii]  # Zero based
                fd.write(format % tuple(nn[norder]))
            fd.write("\n%d # number of parameter values per element\n" % nm_params)
            # Top level always 0?
            fd.write("0 # number of parameters\n")
            fd.write("# Parameters\n\n")
            fd.write("%d # number of domains\n" % sum([mi.shape[0] for mi in mat_ids]))
            fd.write("# Domains\n")
            for mi in mat_ids:
                # Domains in comsol have to be > 0
                if (mi <= 0).any():
                    mi += mi.min() + 1
                for dom in mi:
                    fd.write("%d\n" % abs(dom))
            fd.write("\n0 # number of up/down pairs\n")
            fd.write("# Up/down\n")

        fd = open(filename, "w")

        coors, ngroups, conns, mat_ids, desc = mesh._get_io_data()

        n_nod, dim = coors.shape

        # Header
        fd.write("# Created by SfePy\n\n\n")
        fd.write("# Major & minor version\n")
        fd.write("0 1\n")
        fd.write("1 # number of tags\n")
        fd.write("# Tags\n")
        fd.write("2 m1\n")
        fd.write("1 # number of types\n")
        fd.write("# Types\n")
        fd.write("3 obj\n\n")

        # Record
        fd.write("# --------- Object 0 ----------\n\n")
        fd.write("0 0 1\n")  # version unused serializable
        fd.write("4 Mesh # class\n")
        fd.write("1 # version\n")
        fd.write("%d # sdim\n" % dim)
        fd.write("%d # number of mesh points\n" % n_nod)
        fd.write("0 # lowest mesh point index\n\n")  # Always zero in SfePy

        fd.write("# Mesh point coordinates\n")

        format = self.get_vector_format(dim) + "\n"
        for ii in range(n_nod):
            nn = tuple(coors[ii])
            fd.write(format % tuple(nn))

        fd.write("\n%d # number of element types\n\n\n" % len(conns))

        for ig, conn in enumerate(conns):
            if desc[ig] == "2_4":
                write_elements(
                    fd, ig, conn, mat_ids, "4 quad", 4, "%d %d %d %d\n", [0, 1, 3, 2], 8
                )

            elif desc[ig] == "2_3":
                # TODO: Verify number of parameters for tri element
                write_elements(
                    fd, ig, conn, mat_ids, "3 tri", 3, "%d %d %d\n", [0, 1, 2], 4
                )

            elif desc[ig] == "3_4":
                # TODO: Verify number of parameters for tet element
                write_elements(
                    fd, ig, conn, mat_ids, "3 tet", 4, "%d %d %d %d\n", [0, 1, 2, 3], 16
                )

            elif desc[ig] == "3_8":
                write_elements(
                    fd,
                    ig,
                    conn,
                    mat_ids,
                    "3 hex",
                    8,
                    "%d %d %d %d %d %d %d %d\n",
                    [0, 1, 3, 2, 4, 5, 7, 6],
                    24,
                )

            else:
                raise ValueError("unknown element type! (%s)" % desc[ig])

        fd.close()

        if out is not None:
            for key, val in six.iteritems(out):
                raise NotImplementedError


if __name__ == "__main__":
    reader = ComsolMeshIO()
    mesh = reader.read_txt(
        "/Users/marcussvensson/Desktop/B71_20_mm_final_180529.mphtxt"
    )
    mesh.write("")

    pause = True
