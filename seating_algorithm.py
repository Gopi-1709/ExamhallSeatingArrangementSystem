from collections import deque

# ------------------------------
# ZIGZAG SEAT PATH GENERATOR
# ------------------------------

def generate_zigzag_path(rows, cols):

    path = []

    for r in range(rows):

        if r % 2 == 0:
            for c in range(cols):
                path.append((r, c))
        else:
            for c in reversed(range(cols)):
                path.append((r, c))

    return path


# ------------------------------
# DEPARTMENT ROTATION GENERATOR
# ------------------------------

def department_rotation(dept_students):

    queues = {
        dept: deque(students)
        for dept, students in dept_students.items()
        if students
    }

    while queues:

        for dept in list(queues.keys()):

            if queues[dept]:
                yield queues[dept].popleft(), dept
            else:
                del queues[dept]


# ------------------------------
# SEAT FILLING WITH RULE CHECK
# ------------------------------

def fill_seats_zigzag(rows, cols, dept_students):

    seating = [[None for _ in range(cols)] for _ in range(rows)]

    zigzag_path = generate_zigzag_path(rows, cols)

    rotator = department_rotation(dept_students)

    for (r, c) in zigzag_path:

        placed = False
        attempts = 0

        while not placed and attempts < 20:

            try:
                student, dept = next(rotator)
            except StopIteration:
                return seating

            # LEFT CHECK
            if c > 0 and seating[r][c-1] is not None:
                if seating[r][c-1][1] == dept:
                    attempts += 1
                    continue

            # TOP CHECK
            if r > 0 and seating[r-1][c] is not None:
                if seating[r-1][c][1] == dept:
                    attempts += 1
                    continue

            seating[r][c] = (student, dept)
            placed = True

    return seating