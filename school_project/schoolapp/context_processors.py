def menu_links(request):
    menu = [
        {'name': 'Dashboard', 'url_name': 'dashboard'},
        {'name': 'Student Tasks', 'url_name': 'student_tasks'},
        # Masalan, dinamik parametrlarsiz
        {'name': 'Teacher Tasks', 'url_name': 'teacher_tasks'},
        {'name': 'Teacher Submissions', 'url_name': 'teacher_submit_task_list'},
        {'name': 'Courses', 'url_name': 'course_view'},
        {'name': 'Enrollments', 'url_name': 'enrollment_list'},
        {'name': 'Login', 'url_name': 'login'},
        {'name': 'Logout', 'url_name': 'logout'},
    ]
    return {'menu_links': menu}
