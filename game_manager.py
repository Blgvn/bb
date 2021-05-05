from map import Map
from file_io import FileIO
from constants import Consts
from screen_manager import Display
from state import State
from node import Node
import time


class GameManager:

    map: Map
    init_state: State

    def __init__(self):
        self.map = None
        self.init_state = None
        self.display = None

        # Reading map file
        self.parse_map()

        # After parsing map it's time to start pygame
        self.display = Display(self.map)

    def parse_map(self):
        map_array = FileIO.read_line_by_line(Consts.MAP_FILE)
        sizes = map_array.pop(0)
        h, w = int(sizes[0]), int(sizes[1])
        self.map = Map(h, w)

        # Variables to read from map
        butters = []
        points = []
        robot = (0, 0)
        for j, row in enumerate(map_array):
            for i, col in enumerate(row):

                # If there is an object in map
                if len(col) > 1:
                    if col[1] == 'b':
                        butters.append((j, i))
                    elif col[1] == 'p':
                        points.append((j, i))
                    elif col[1] == 'r':
                        robot = (j, i)
                    row[i] = col[0]

            # Append row to map
            self.map.append_row(row)

        # Setting map and init state
        self.map.set_points(points)
        self.init_state = State(robot, butters)

    def start_search(self, search_type: str) -> list[State]:
        result = self.__getattribute__(search_type + '_search')()

        # Putting path to goal in list
        if search_type == 'bd_bfs':
            list1 = GameManager.extract_path_list(result[0])
            list1.reverse()
            list2 = GameManager.extract_path_list(result[1])
            list1.extend(list2)
            return list1
        else:
            result_list = GameManager.extract_path_list(result)
            result_list.reverse()
            return result_list

    def display_states(self, states_list: list[State]) -> None:
        if len(states_list) <= 0:
            raise Exception('There is no way.')
        # Starting display
        self.display.update(self.init_state)
        self.display.begin_display()

        for state in states_list:
            time.sleep(Consts.STEP_TIME)
            self.display.update(state)

    def bd_bfs_search(self) -> (Node, Node):

        frontier1 = [Node(self.init_state, None, 0, None, 0)]
        frontier2 = []
        visited1 = {}
        visited2 = {}

        # Putting Butters into points
        new_butters = self.init_state.butters.copy()
        for i, point in enumerate(self.map.points):
            new_butters[i] = point

        # Putting the robot in all possible positions around butter
        for i, point in enumerate(self.map.points):
            for direction in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                new_y = point[0] + direction[0]
                new_x = point[1] + direction[1]

                # Checking out of bounds or blocks
                if self.map.check_out_of_bounds(new_y, new_x) or self.map.is_block(new_y, new_x):
                    continue

                # Checking butters around butter
                if (new_y, new_x) in new_butters:
                    continue

                state = State((new_y, new_x), new_butters.copy())
                frontier2.append(Node(state, None, 0, None, 0))

        # Starting BFS
        while len(frontier1) > 0 and len(frontier2) > 0:
            node1 = frontier1.pop(0)
            # To handle shortest path
            if node1.state not in visited1:
                visited1[node1.state] = node1

            self.display.update(node1.state)
            time.sleep(0.3)

            node2 = frontier2.pop(0)
            # To handle shortest path
            if node2.state not in visited2:
                visited2[node2.state] = node2

            self.display.update(node2.state)
            time.sleep(0.3)
            # If we reach from initial state to goal
            if node2.state in visited1:
                return visited1[node2.state], node2

            # If we reach from goal to initial state
            if node1.state in visited2:
                return node1, visited2[node1.state]

            actions1 = State.successor(node1.state, self.map)
            frontier1.extend(node1.expand(actions1))
            actions2 = State.successor(node2.state, self.map, reverse=True)
            frontier2.extend(node2.expand(actions2))

    def ids_search(self) -> Node:
        # Implementation of DLS to be used in IDS
        def dls_search(limit: int, depth: int, node: Node) -> Node:
            """ This DLS implementation is used in IDS search.
                :param limit: Maximum depth
                :param depth: The explored depth until now
                :param node: The node the expand next
                :returns Node of goal if Goal state is found"""

            if time.time() - cur_time > 30.0:
                raise Exception('Time limit exceeded')

            # display.update(node.state)
            # time.sleep(0.08)

            res = None
            if depth < limit and node.state not in visited_states:
                actions = State.successor(node.state, self.map)
                # print(actions)
                visited_states[node.state] = True
                for child in node.expand(actions)[::-1]:

                    if State.is_goal(child.state, self.map.points):
                        return child

                    # Recursive calling
                    r = dls_search(limit, depth + 1, child)
                    if r is not None:
                        res = r
                        break

                    # To avoid adding non-visited states into visited states list
                    if child.state in visited_states:
                        del visited_states[child.state]

            return res

        # IDS Implementation
        for i in range(Consts.FIRST_K, Consts.LAST_K):
            print('Starting with depth', i)
            cur_time = time.time()
            root_node = Node(self.init_state, None, 0, None, 0)
            visited_states = {}
            result = dls_search(i, 0, root_node)
            if result is not None:
                return result
        # If there is no result in IDS
        return None

    @staticmethod
    def extract_path_list(node: Node) -> list[State]:
        result_list = []
        watchdog = 0
        while node is not None:
            watchdog += 1
            if watchdog > 1000:
                raise Exception('Watchdog limit exceeded')
            result_list.append(node.state)
            node = node.parent

        return result_list