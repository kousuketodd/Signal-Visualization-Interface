from typing import Dict, Any, Tuple, Optional

import numpy

from payload import Payload



class Heatmap:

    # ONLY NEED THE MOST RECENT VALUES FROM THE PAYLOAD -> payload.get_most_recent_data()
    def __init__(self, payload: Payload, ro=None):
        self.payload_entree = payload.get_most_recent_data()
        self.ro = ro

    # Calculating the points for the heatmap from the diagonal resistance values for like the 5x41 materials
    # -> CAN HAVE DIFFERENT HORIZONTAL WIDTH BUT SAME OVERALL STRUCTURE OF THE 5x41 and SAME HEIGHT/DEPTH OF 5
    def calc_pts_diagonal(self, switcher: Dict[str, Tuple]) -> numpy.ndarray:
        mapped_pts: Dict[Tuple[int, int], float] = self._mapping_coord(switcher)
        width_list = [k[0] for k in mapped_pts]
        if width_list is None:
            max_width = 0
        else:
            max_width = max(width_list)
        max_height = 4

        # OUTPUT 2D MATRIX WILL HAVE THE DIMENSION: max_width*2 (to account for the half points in the intersections)
        # OUTPUTS WILL BE MAPPED AT TWICE THE COLUMN DIMENSION AND REFLECTED ONCE AT THE PT TO THE LEFT, EXCLUDING
        # THE OUTER MOST PTS
        # THE EXCEPTION CASE, SHIFT RIGHT: (0,0) -> (0,0),(0,1);
        # GENERAL CASE, SHIFT LEFT: (0,2) -> (0,3)(0,4) & (0,3) -> (0,6) (0,5)
        # x max_height
        depth = max_height
        rows = depth + 1
        cols = max_width * 2 + 1
        output_matrix = numpy.full((rows, cols), -1.0, dtype=float)

        real_vals = sorted({r for (r, _) in mapped_pts})

        # THE ITERATION IS BASED ON THE DIAGONAL LINES FROM TOP LEFT (OF NORMAL) TO BOTTOM RIGHT (OF PRIME)
        for norm_num in real_vals:  # 1, 2, ..., max_width
            # BASE CASE is valid where the PTS: (MIN #, MIN #'-4) to (#+4 EXIST) SINCE DEPTH in the Y-AXIS IS 4 DEEP
            # (0-4) GOING THROUGH THE DIAGONALS THAT GO FROM THE LEFT OF THE REAL #s to the RIGHT of the PRIMED #s
            # e.g. (3,5')

            prim_num = norm_num + (max_height // 2)
            # LOWER BOUND IS PRIME_NUM >= 5 b/c STARTS @ 1 NOT 0
            # BASE CASE INTERCEPTS
            if (norm_num < prim_num) and (prim_num >= max_height + 1) and (norm_num <= max_width - max_height):
                for i in range(max_height + 1):
                    key_a = (norm_num, prim_num)
                    key_b = (norm_num + i, prim_num - 4 + i)
                    # print(f"FOR key_a={key_a}, key_b={key_b} @ [{i},{(norm_num + i) + norm_num}] &"
                    # f" @ [{i},{(norm_num + i) + norm_num - 1}]")

                    if key_a in mapped_pts and key_b in mapped_pts:
                        output_matrix[i][(norm_num + i) + norm_num] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2
                    else:
                        raise RuntimeError(f"HEATMAP CALC. ERROR, KEY DOESN'T EXIST: KEY_A= {key_a}, KEY_B= {key_b}")

            # EDGE CASE NOT THE OUTERMOST
            elif (norm_num < prim_num) and (prim_num <= max_width):

                # RIGHT SIDE: 18-19
                if (max_width - norm_num) < norm_num:
                    itr = max_width - norm_num + 1
                    for i in range(itr):
                        key_a = (norm_num, prim_num)
                        key_b = (norm_num + i, prim_num - 4 + i)

                        # print(f"FOR key_a={key_a}, key_b={key_b} @ [{i},{(norm_num + i) + norm_num}] &"
                        #       f" @ [{i},{(norm_num + i) + norm_num - 1}]")

                        output_matrix[i][(norm_num + i) + norm_num] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2

                # LEFT SIDE
                else:
                    itr = norm_num + (max_height // 2)

                    # GO FROM BOTTOM TO TOP INSTEAD
                    for j in range(itr):
                        i = max_height - j
                        key_a = (norm_num, prim_num)
                        key_b = (norm_num + i, prim_num - 4 + i)

                        # print(f"FOR key_a={key_a}, key_b={key_b} @ [{i},{(norm_num + i) + norm_num}] &"
                        #       f" @ [{i},{(norm_num + i) + norm_num - 1}]")

                        output_matrix[i][(norm_num + i) + norm_num] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2

        # FOR THE EDGE CASES
        # PTS W/ NO INTERSECTIONS
        # 2-4'
        k = 2
        key_a = (k, k + (max_height // 2))

        output_matrix[0][k * 2] = mapped_pts[key_a]

        # 20-18'
        k = max_width - 1
        key_a = (k, k - (max_height // 2))

        output_matrix[0][k * 2] = mapped_pts[key_a]

        # 2-4'
        k = 2
        key_a = (k, k + (max_height // 2))

        output_matrix[max_height][k * 2] = mapped_pts[key_a]

        # 18-20'
        k = max_width - 1
        key_a = (k - (max_height // 2), k)

        output_matrix[max_height][k * 2] = mapped_pts[key_a]

        # 1-1'
        k = 1
        key_a = (1, 1)
        key_b = (1, 1 + (max_height // 2))

        output_matrix[0][k * 2] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2

        # 3-1'
        k = 1
        key_a = (1, 1)
        key_b = (1, 3)

        output_matrix[max_height][k * 2] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2

        # ONLY IF THE FULL CONFIGURATION OF SENSOR SINCE THIS IS THE ONLY VERTICAL COMPONENTS
        if max_width == 22:
            # 21-19'
            k = max_width
            key_a = (k, k - (max_height // 2))
            key_b = (k, k)

            output_matrix[0][k * 2] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2

            # 19-21'
            k = max_width
            key_a = (k - (max_height // 2), k)
            key_b = (k, k)

            output_matrix[max_height][k * 2] = (mapped_pts[key_a] + mapped_pts[key_b]) / 2

        # FILL IN THE WHITESPACE BETWEEN EACH OF THE PTS W/ THE SURROUNDING AVERAGES
        baseline = output_matrix.copy()
        for y in range(rows):
            for x in range(cols):
                if baseline[y, x] == -1:
                    neigh_vals = []

                    # top
                    if y > 0 and baseline[y - 1, x] != -1:
                        neigh_vals.append(baseline[y - 1, x])
                    # bottom
                    if y < rows - 1 and baseline[y + 1, x] != -1:
                        neigh_vals.append(baseline[y + 1, x])
                    # left
                    if x > 0 and baseline[y, x - 1] != -1:
                        neigh_vals.append(baseline[y, x - 1])
                    # right
                    if x < cols - 1 and baseline[y, x + 1] != -1:
                        neigh_vals.append(baseline[y, x + 1])

                    if neigh_vals:
                        output_matrix[y, x] = sum(neigh_vals) / len(neigh_vals)

        return output_matrix

    # RETURNS THE mapping according to the SWITCHER PARAMETER configuration for each col name
    # like 6001 (ohm) = 1 - 1p or (1,1)
    # use coord (tuple) for mapping where (# real number, # prime number) to represent the diagonals -> 2-4p is (2,4)
    # float value is the associated resistance value of the line
    def _mapping_coord(self, switcher: Dict[str, Tuple]) -> Dict[Tuple[int, int], float]:
        map_result: Dict[Tuple[int, int], float] = {}
        for raw_key in self.payload_entree.keys():
            # key = raw_key.strip()
            convert_key: Tuple[int, int] = switcher.get(raw_key, None)

            if convert_key is not None:

                # CHECK NEED TO DO THE BASE RESISTANCE CALC. FOR DERV.
                if self.ro is None:
                    map_result[convert_key] = self.payload_entree[raw_key]
                else:
                    map_result[convert_key] = (self.payload_entree[raw_key] - self.ro) / self.ro
            else:
                raise RuntimeError(f"Unknown key {raw_key}, not following the Header format: {switcher.keys()}."
                                   f"THE HEADER FORMAT ENTERED HAS TO MATCH THE CONST. SWITCHER FOR MAPPING"
                                   f"-> CHANGE 'program_configrations.py' to fix.")
        return map_result

    # UPDATE THE HEATMAP'S PAYLOAD ENTRE that's being used
    def set_payload_entree(self, payload_entree: Dict[str, Any]):
        self.payload_entree = payload_entree
