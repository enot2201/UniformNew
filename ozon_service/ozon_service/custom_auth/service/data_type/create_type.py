from dataclasses import dataclass


@dataclass
class UserData:
    """
    Данные для создания пользователя +
    """
    phone_number: str
    gender: str
    name: str
    surname: str
    id: str = None
    date_birth: str = None
    avatar_id: str = None


@dataclass
class StudentData:
    """
    Данные для создания студента +
    """
    id: str = None
    user_id: str = None
    group_id: str = None
    is_headman: bool = False


@dataclass
class TeacherData:
    """
    Данные для создания преподователя +
    """
    user_id: str
    id: str = None
    is_lead_department: bool = False


@dataclass
class UniversityData:
    """
    Данные для создания университета +
    """
    name: str
    city: str
    id: str = None


@dataclass
class DepartmentData:
    """
    Данные для создания кафедры +
    """
    name: str
    course: str
    university: str = None
    id: str = None


@dataclass
class GroupData:
    """
    Данные для создания учебной группы +
    """
    name: str
    course: str
    type_education: str
    direction: str
    university: str = None
    id: str = None


@dataclass
class DisciplineData:
    """
    Данные для создания дисциплины +
    """
    name: str
    university: str = None
    id: str = None


@dataclass
class TeacherDepartmentData:
    """
    Данные для создания связи препода и кафедры
    """
    department_id: id = None
    teacher_id: id = None
    id: str = None


@dataclass
class StudentsGroupsData:
    """
    Данные для создания связи студента и группы
    """
    student_id: id = None
    group_id: id = None
    id: str = None


@dataclass
class DisciplinesTeacherData:
    """
    Данные для создания DisciplinesTeacher
    """
    discipline_id: str
    teacher_id: str
    id: str = None
