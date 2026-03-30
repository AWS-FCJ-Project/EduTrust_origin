import {
    Home, FileText, Trophy, MessageSquare,
    Folder, Layers, Users, BookOpen, Library, Lightbulb, XCircle, UserPlus, GraduationCap, ShieldCheck
} from 'lucide-react';

export const MENU_CONFIG = {
    student: [
        { label: "Trang chủ", icon: <Home size={22} />, desc: "Tổng quan về học tập", path: "/dashboard" },
        { label: "Thư viện tài liệu", icon: <FileText size={22} />, desc: "Các bài giảng và tài liệu học", path: "/dashboard/resources" },
        { label: "Bài tập", icon: <Library size={22} />, desc: "Bài tập về nhà và ôn luyện", path: "/dashboard/my_exams" },
        { label: "Bài thi", icon: <BookOpen size={22} />, desc: "Đề thi", path: "/dashboard/exam_list" },
        { label: "Kết quả", icon: <Trophy size={22} />, desc: "Kết quả học tập", path: "/dashboard/ket-qua" },
        { label: "AI hỗ trợ", icon: <MessageSquare size={22} />, desc: "Hỗ trợ học tập bằng AI", path: "/dashboard/chat_ai" },
        { label: "Giám sát Camera", icon: <Lightbulb size={22} />, desc: "Test tính năng giám sát", path: "/dashboard/test-camera" },
    ],
    admin: [
        { label: "Trang chủ", icon: <Home size={22} />, desc: "Tổng quan", path: "/dashboard" },
        { label: "Tạo tài khoản", icon: <UserPlus size={22} />, desc: "Quản trị người dùng", path: "/dashboard/management" },
        { label: "Admin", icon: <ShieldCheck size={22} />, desc: "Quản lý ban quản trị", path: "/dashboard/admins" },
        { label: "Giáo viên", icon: <Users size={22} />, desc: "Quản lý giáo viên", path: "/dashboard/teachers" },
        { label: "Học sinh", icon: <GraduationCap size={22} />, desc: "Quản lý học sinh", path: "/dashboard/students" },
        { label: "Lớp học", icon: <Layers size={22} />, desc: "Quản lý lớp học", path: "/dashboard/classes" },
        { label: "Đề thi", icon: <Folder size={22} />, desc: "Quản lý đề thi", path: "/dashboard/exams" },
        { label: "Kết quả", icon: <Trophy size={22} />, desc: "Thống kê kết quả thi", path: "/dashboard/exams/results" },
        { label: "Vi phạm", icon: <XCircle size={22} />, desc: "Hồ sơ vi phạm toàn trường", path: "/dashboard/violations" },
        { label: "AI hỗ trợ", icon: <MessageSquare size={22} />, desc: "Trợ lý ảo thông minh", path: "/dashboard/chat_ai" },
        { label: "Giám sát Camera", icon: <Lightbulb size={22} />, desc: "Test tính năng giám sát", path: "/dashboard/test-camera" },
    ],
    teacher: [
        { label: "Trang chủ", icon: <Home size={22} />, desc: "Tổng quan", path: "/dashboard" },
        { label: "Đề thi", icon: <Folder size={22} />, desc: "Quản lý đề thi", path: "/dashboard/exams" },
        { label: "Lớp học", icon: <Layers size={22} />, desc: "Quản lý lớp học tại đây", path: "/dashboard/classes" },
        { label: "Thư viện tài liệu", icon: <BookOpen size={22} />, desc: "Kho học liệu", path: "/dashboard/resources" },
        { label: "Vi phạm", icon: <XCircle size={22} />, desc: "Theo dõi vi phạm lớp chủ nhiệm", path: "/dashboard/violations" },
        { label: "Kết quả", icon: <Trophy size={22} />, desc: "Báo cáo điểm số", path: "/dashboard/exams/results" },
        { label: "AI hỗ trợ", icon: <MessageSquare size={22} />, desc: "Trợ lý giảng dạy AI", path: "/dashboard/chat_ai" },
        { label: "Giám sát Camera", icon: <Lightbulb size={22} />, desc: "Test tính năng giám sát", path: "/dashboard/test-camera" },
    ]
};
