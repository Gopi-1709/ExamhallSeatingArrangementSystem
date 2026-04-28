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



# from collections import deque


# # ------------------------------
# # ZIGZAG PATH
# # ------------------------------
# def generate_zigzag_path(rows, cols):
#     path = []
#     for r in range(rows):
#         if r % 2 == 0:
#             for c in range(cols):
#                 path.append((r, c))
#         else:
#             for c in reversed(range(cols)):
#                 path.append((r, c))
#     return path


# # ------------------------------
# # ROUND ROBIN ROTATION
# # ------------------------------
# def department_rotation(dept_students):
#     queues = {
#         dept: deque(students)
#         for dept, students in dept_students.items()
#         if students
#     }

#     while queues:
#         for dept in list(queues.keys()):
#             if queues[dept]:
#                 yield queues[dept].popleft(), dept
#             else:
#                 del queues[dept]


# # ------------------------------
# # SUBJECT-BASED SEATING ENGINE
# # ------------------------------
# def fill_seats_zigzag(rows, cols, dept_students, dept_subject):

#     seating = [[None for _ in range(cols)] for _ in range(rows)]
#     zigzag_path = generate_zigzag_path(rows, cols)

#     rotator = department_rotation(dept_students)

#     for (r, c) in zigzag_path:

#         placed = False
#         attempts = 0

#         while not placed and attempts < 30:

#             try:
#                 student, dept = next(rotator)
#             except StopIteration:
#                 return seating

#             current_subject = dept_subject.get(dept)

#             # LEFT CHECK
#             if c > 0 and seating[r][c-1] is not None:
#                 left_student, left_dept = seating[r][c-1]
#                 left_subject = dept_subject.get(left_dept)

#                 if left_subject == current_subject:
#                     attempts += 1
#                     continue

#             # TOP CHECK
#             if r > 0 and seating[r-1][c] is not None:
#                 top_student, top_dept = seating[r-1][c]
#                 top_subject = dept_subject.get(top_dept)

#                 if top_subject == current_subject:
#                     attempts += 1
#                     continue

#             # ✅ PLACE STUDENT
#             seating[r][c] = (student, dept)
#             placed = True

#         # 🔥 FINAL FALLBACK (when no valid placement possible)
#         if not placed:
#             for d in dept_students:
#                 if dept_students[d]:
#                     student = dept_students[d].pop(0)
#                     seating[r][c] = (student, d)
#                     break

#     return seating



# from collections import deque

# def generate_zigzag_path(rows, cols):
#     path = []
#     for r in range(rows):
#         if r % 2 == 0:
#             for c in range(cols):
#                 path.append((r, c))
#         else:
#             for c in reversed(range(cols)):
#                 path.append((r, c))
#     return path



# from collections import deque

# def fill_seats_zigzag(rows, cols, dept_students, dept_subject):

#     seating = [[None for _ in range(cols)] for _ in range(rows)]

#     # Zigzag path
#     path = []
#     for r in range(rows):
#         if r % 2 == 0:
#             for c in range(cols):
#                 path.append((r, c))
#         else:
#             for c in reversed(range(cols)):
#                 path.append((r, c))

#     # Convert to queues ONCE
#     queues = {
#         dept: deque(students)
#         for dept, students in dept_students.items()
#         if students
#     }

#     dept_list = list(queues.keys())
#     index = 0

#     for (r, c) in path:

#         best_dept = None
#         best_score = float('inf')

#         for _ in range(len(dept_list)):

#             dept = dept_list[index % len(dept_list)]
#             index += 1

#             if not queues.get(dept) or not queues[dept]:
#                 continue

#             current_subject = dept_subject.get(dept)

#             score = 0

#             # LEFT CHECK
#             if c > 0 and seating[r][c-1]:
#                 left_dept = seating[r][c-1][1]

#                 if dept_subject.get(left_dept) == current_subject:
#                     score += 100   # ❗ HIGH PENALTY (same subject)
#                 elif left_dept == dept:
#                     score += 5     # small penalty (same dept)

#             # TOP CHECK
#             if r > 0 and seating[r-1][c]:
#                 top_dept = seating[r-1][c][1]

#                 if dept_subject.get(top_dept) == current_subject:
#                     score += 100
#                 elif top_dept == dept:
#                     score += 5

#             if score < best_score:
#                 best_score = score
#                 best_dept = dept

#         # PLACE
#         if best_dept:
#             student = queues[best_dept].popleft()
#             seating[r][c] = (student, best_dept)

#     return seating, queues