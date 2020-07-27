import numpy as np
import heapq

# The A* algorithm can find the shortest path between 2 given anchors.
# Input the coordinates of these anchors as start and end.

class State:

    # TODO: import design
    # TODO: Find a good way of determining step size (fast runtime + no overshooting)
    
    def __init__(self, direction, coord, origin, step_size=1):
        self.neighbors = []
        self.step_size = step_size
        self.direction = direction
        self.coord = coord # 2D numpy array of the form np.array([xi, yi]) showing current position
        if origin: # the last State object created prior to coord
            # coord is not the first point on this path
            if len(origin.path) > 1:
                x_ult, y_ult = origin.path[-1] # last point on origin's path
                x_pen, y_pen = origin.path[-2] # penultimate point on origin's path
                x_cur, y_cur = self.coord
                if (y_ult - y_pen) * (x_cur - x_ult) == (y_cur - y_ult) * (x_ult - x_pen):
                    # Concatenate collinear line segments (joined at a point and have identical slopes)
                    self.path = origin.path[:-1] + [coord]
                else:
                    self.path = origin.path + [coord]
            else:
                self.path = origin.path + [coord]
        else:
            # coord is the first point on this path
            self.path = [coord]

    def get_neighbors(self):
        # Look in forward, left, and right directions a fixed distance away.
        # If the lines segment connecting the current point and this next one does
        # not collide with any bounding boxes in design.components, add it to the
        # list of neighbors.
        # The dot product between direction and the vector connecting the current
        # point and a potential neighbor must be non-negative to avoid retracing.
        for disp in [np.array([0, 1]), np.array([0, -1]), np.array([1, 0]), np.array([-1, 0])]:
            # Unit displacement in 4 cardinal directions
            if np.dot(disp, self.direction) >= 0:
                # Ignore backward direction
                curpt = self.path[-1]
                nextpt = curpt + self.step_size * disp
                # Check to see whether line segment connecting these 2 points intersects any other
                # pair of points constituting the bounding box of any component in design
                suitable = True # flag indicating absence of intersections
                for component in design.components:
                    xmin, ymin, xmax, ymax = design.components[component].qgeometry_bounds()
                    # p, q, r, s are corner coordinates of each bounding box
                    p, q, r, s = [np.array([xmin, ymin]), 
                                np.array([xmin, ymax]), 
                                np.array([xmax, ymin]), 
                                np.array([xmax, ymax])]
                    if any(self.overlapping(curpt, nextpt, k, l) for k, l in [(p, q), (p, r), (r, s), (q, s)]):
                        # At least 1 intersection present; do not proceed!
                        suitable = False
                        break     
                if suitable:
                    self.neighbors.append(nextpt)
    
    def overlapping(self, a, b, c, d):
        # Returns whether segment ab intersects or overlaps with segment cd, where a, b, c, and d are all coordinates
        x0_start, y0_start = a
        x0_end, y0_end = b
        x1_start, y1_start = c
        x1_end, y1_end = d
        if (x0_start == x0_end) and (x1_start == x1_end):
            # 2 vertical lines intersect only if they completely overlap at some point(s)
            if x0_end == x1_start:
                # Same x-intercept -> potential overlap, so check y coordinate
                return not (min(y0_start, y0_end) > max(y1_start, y1_end) or (min(y1_start, y1_end) > max(y0_start, y1_end)))
            else:
                # Parallel lines with different x-intercepts don't overlap
                return False
        elif (x0_start == x0_end) or (x1_start == x1_end):
            # One segment is vertical, the other is not
            # Express non-vertical line in the form of y = mx + b and check y value
            if x1_start == x1_end:
                # Exchange names; the analysis below assumes that line 0 is the vertical one
                x0_start, x0_end, x1_start, x1_end = x1_start, x1_end, x0_start, x0_end
                y0_start, y0_end, y1_start, y1_end = y1_start, y1_end, y0_start, y0_end
            m = (y1_end - y1_start) / (x1_end - x1_start)
            b = (x1_end * y1_start - x1_start * y1_end) / (x1_end - x1_start)
            if min(x1_start, x1_end) <= x0_start <= max(x1_start, x1_end):
                if min(y0_start, y0_end) <= m * x0_start + b <= max(y0_start, y0_end):
                    return True
            return False
        else:
            # Neither line is vertical; check slopes and y-intercepts
            b0 = (y0_start * x0_end - y0_end * x0_start) / (x0_end - x0_start) # y-intercept of line 0
            b1 = (y1_start * x1_end - y1_end * x1_start) / (x1_end - x1_start) # y-intercept of line 1
            if (x1_end - x1_start) * (y0_end - y0_start) == (x0_end - x0_start) * (y1_end - y1_start):
                # Lines have identical slopes
                if b0 == b1:
                    # Same y-intercept -> potential overlap, so check x coordinate
                    return not (min(x0_start, x0_end) > max(x1_start, x1_end) or (min(x1_start, x1_end) > max(x0_start, x1_end)))
                else:
                    # Parallel lines with different y-intercepts don't overlap
                    return False 
            else:
                # Lines not parallel so must intersect somewhere -> examine slopes m0 and m1
                m0 = (y0_end - y0_start) / (x0_end - x0_start) # slope of line 0
                m1 = (y1_end - y1_start) / (x1_end - x1_start) # slope of line 1
                x_intersect = (b1 - b0) / (m0 - m1) # x coordinate of intersection point
                y_intersect = m0 * x_intersect + b0 # y coordinate of intersection point
                if min(x0_start, x0_end) <= x_intersect <= max(x0_start, x0_end):
                    if min(y0_start, y0_end) <= y_intersect <= max(y0_start, y0_end):
                        if min(x1_start, x1_end) <= x_intersect <= max(x1_start, x1_end):
                            if min(y1_start, y1_end) <= y_intersect <= max(y1_start, y1_end):
                                return True
                return False

class AStarSolver:

    def __init__(self, start_direction, start, end, step_size):
        self.path = [] # final answer
        self.visited = set([(start[0], start[1])]) # record of points we've already visited
        self.statemapper = {} # maps tuple(remaining_dist, length_travelled, coordx, coordy) to State object
        self.h = [] # priority queue (heap in Python implementation)
        self.start_direction = start_direction # direction of starting pin normal
        self.start = start # 2D numpy array of the form np.array([xi, yi]) showing initial anchor position
        self.end = end # 2D numpy array of the form np.array([xi, yi]) showing final anchor position
        self.step_size = step_size

    def solve(self):
        startState = State(self.start_direction, self.start, None, self.step_size)
        starting_dist, xi, yi = sum(abs(self.start - self.end)), startState.coord[0], startState.coord[1]
        self.statemapper[(0, starting_dist, xi, yi)] = startState
        heapq.heappush(self.h, (0, starting_dist, xi, yi))
        # Elements in the heap are ordered by the following:
        # 1. The total length of the path from self.start
        # 2. How far they are from the destination (end), measured using Manhattan distance
        # 3. The x coordinate of the latest point
        # 4. The y coordinate of the latest point
        while self.h and not self.path:
            length_travelled, remaining_dist, x, y = heapq.heappop(self.h) # Pop from heap
            current_state = self.statemapper[(length_travelled, remaining_dist, x, y)]
            current_state.get_neighbors() # Find all neighbors in forward, left, and right directions
            for neighbor in current_state.neighbors: # Right now neighbor is a coordinate, not State object
                if tuple(neighbor) not in self.visited:
                    new_remaining_dist = sum(abs(neighbor - self.end))
                    new_length_travelled = length_travelled + self.step_size
                    newState = State(neighbor - current_state.coord, neighbor, current_state, self.step_size) # start and end handled by instantiation
                    nx, ny = newState.coord
                    if not new_remaining_dist:
                        # Destination has been reached
                        self.path = newState.path
                        break
                    heapq.heappush(self.h, (new_length_travelled, new_remaining_dist, nx, ny))
                    self.statemapper[(new_length_travelled, new_remaining_dist, nx, ny)] = newState
                    self.visited.add((nx, ny))
        return self.path