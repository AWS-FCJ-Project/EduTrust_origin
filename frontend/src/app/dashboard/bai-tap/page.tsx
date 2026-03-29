"use client";

import { useState } from 'react';
import {
    Clock, X, Edit3, ListChecks, ChevronRight
} from 'lucide-react';

const AssignmentsPage = () => {
    const [activeTab, setActiveTab] = useState('pending');
    const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const [assignments] = useState([
        {
            id: 1,
            title: "Giải bài tập Giải tích chương 3",
            subject: "Toán học",
            deadline: "Còn 2 giờ",
            status: "pending",
            type: "Tự luận",
            description: "Hoàn thành các bài tập từ trang 45 đến 50 trong sách giáo khoa nâng cao."
        },
        {
            id: 2,
            title: "Kiểm tra 15 phút - Từ vựng Unit 8",
            subject: "Tiếng Anh",
            deadline: "Còn 5 giờ",
            status: "pending",
            type: "Trắc nghiệm",
            questions: [
                { id: 1, question: "What is the synonym of 'Happy'?", options: ["Sad", "Joyful", "Angry", "Bored"] },
                { id: 2, question: "Choose the correct spelling:", options: ["Accomodate", "Accommodate", "Acomodate", "Accommodat"] },
                { id: 3, question: "He ____ to school every day.", options: ["go", "goes", "going", "gone"] }
            ]
        },
        {
            id: 3,
            title: "Bài tập làm văn số 2",
            subject: "Ngữ văn",
            deadline: "Còn 1 ngày",
            status: "pending",
            type: "Tự luận",
            description: "Nghị luận về tư tưởng đạo lý trong đoạn trích sau..."
        }
    ]);

    const filteredAssignments = assignments.filter(item => item.status === activeTab);

    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-gray-800 tracking-tight">Cổng Học Tập</h1>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">Danh sách bài tập & nhiệm vụ</p>
                </div>

                <div className="flex gap-1 bg-white p-1 rounded-xl shadow-sm border border-gray-100 shrink-0">
                    <TabButton label="Chưa nộp" active={activeTab === 'pending'} onClick={() => setActiveTab('pending')} />
                    <TabButton label="Đã xong" active={activeTab === 'submitted'} onClick={() => setActiveTab('submitted')} />
                </div>
            </div>

            {/* Grid Layout */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                {filteredAssignments.map((assignment) => (
                    <AssignmentCard
                        key={assignment.id}
                        data={assignment}
                        onAction={() => { setSelectedAssignment(assignment); setIsModalOpen(true); }}
                    />
                ))}
            </div>

            {/* Submission Modal */}
            {isModalOpen && (
                <ActionModal
                    assignment={selectedAssignment}
                    onClose={() => setIsModalOpen(false)}
                />
            )}
        </div>
    );
};

// --- Sub-components for cleaner codebase ---

const AssignmentCard = ({ data, onAction }: { data: Assignment, onAction: () => void }) => {
    const isQuiz = data.type === 'Trắc nghiệm';

    return (
        <div className="bg-white rounded-2xl p-5 border border-transparent shadow-sm hover:shadow-md hover:border-[#5B0019]/10 transition-all group flex flex-col justify-between h-full">
            <div>
                <div className="flex justify-between items-start mb-4">
                    <div className={`p-3 rounded-xl ${isQuiz ? 'bg-[#5B0019]/5 text-[#5B0019]' : 'bg-gray-50 text-gray-600'}`}>
                        {isQuiz ? <ListChecks size={22} /> : <Edit3 size={22} />}
                    </div>
                    <div className="flex items-center gap-1.5 px-3 py-1 bg-orange-50 text-orange-600 rounded-lg text-[10px] font-black uppercase">
                        <Clock size={12} /> {data.deadline}
                    </div>
                </div>

                <h3 className="font-bold text-gray-800 text-base group-hover:text-[#5B0019] transition-colors line-clamp-1">
                    {data.title}
                </h3>
                <p className="text-xs font-bold text-gray-400 mt-1 uppercase tracking-wider">{data.subject}</p>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between">
                <span className="text-[10px] font-bold text-gray-400 uppercase italic">Loại: {data.type}</span>
                <button
                    onClick={onAction}
                    className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-black bg-[#5B0019] text-white hover:bg-[#7a0022] transition-all active:scale-95"
                >
                    {isQuiz ? 'LÀM BÀI' : 'NỘP BÀI'} <ChevronRight size={14} />
                </button>
            </div>
        </div>
    );
};

const TabButton = ({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) => (
    <button
        onClick={onClick}
        className={`px-4 py-2 rounded-lg text-xs font-black transition-all ${active
            ? 'bg-[#5B0019] text-white shadow-md'
            : 'text-gray-500 hover:bg-gray-50'
            }`}
    >
        {label}
    </button>
);

interface Assignment {
    id: number; title: string; subject: string; deadline: string;
    status: string; type: string; description?: string;
    questions?: { id: number; question: string; options: string[] }[];
}

const ActionModal = ({ assignment, onClose }: { assignment: Assignment | null, onClose: () => void }) => {
    if (!assignment) return null;
    return (
        <div className="fixed inset-0 z-100 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h2 className="font-black text-gray-800 uppercase tracking-tight">Chi tiết nhiệm vụ</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><X size={18} /></button>
                </div>
                <div className="p-8 max-h-[70vh] overflow-y-auto">
                    {/* Modal Content */}
                    <h3 className="text-xl font-bold mb-4">{assignment.title}</h3>
                    <p className="text-sm text-gray-500 mb-6">{assignment.description}</p>
                    <textarea
                        className="w-full h-40 p-4 bg-gray-50 border-2 border-gray-100 rounded-2xl outline-none focus:border-[#5B0019]/20 transition-all"
                        placeholder="Nhập nội dung bài làm..."
                    />
                </div>
                <div className="p-6 bg-gray-50 flex justify-end gap-3">
                    <button onClick={onClose} className="px-6 py-2 text-sm font-bold text-gray-400">ĐÓNG</button>
                    <button className="px-8 py-2 bg-[#5B0019] text-white text-sm font-black rounded-xl">XÁC NHẬN NỘP</button>
                </div>
            </div>
        </div>
    );
};

export default AssignmentsPage;
