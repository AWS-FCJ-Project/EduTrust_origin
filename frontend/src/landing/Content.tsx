"use client";

import { Section } from "@/components/ui/section";
import { useEffect, useState } from "react";
import {
    Carousel,
    CarouselContent,
    CarouselItem,
    CarouselNext,
    CarouselPrevious,
} from "@/components/ui/carousel";
import pic1 from "../../public/pic1.png";
import pic2 from "../../public/pic2.png";
import pic3 from "../../public/pic3.png";
import experience from "../../public/experience.png";
import study from "../../public/study.png";
import sport from "../../public/sport.png";
import art from "../../public/art.png";
import Image from "next/image";

export default function Content() {
    const [activeSection, setActiveSection] = useState("hero");
    const sectionIds = ["hero", "section-1", "section-2", "section-3", "section-4"];

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) setActiveSection(entry.target.id);
                });
            },
            { threshold: 0.6 }
        );

        sectionIds.forEach((id) => {
            const el = document.getElementById(id);
            if (el) observer.observe(el);
        });

        return () => observer.disconnect();
    }, []);

    return (
        <div className="relative">
            <nav className="fixed right-6 top-1/2 -translate-y-1/2 z-50 flex flex-col gap-4">
                {sectionIds.map((id) => (
                    <a
                        key={id}
                        href={`#${id}`}
                        className={`w-3 h-3 rounded-full border border-black transition-all ${activeSection === id ? "bg-black scale-125" : "bg-transparent opacity-30"
                            }`}
                    />
                ))}
            </nav>

            <main className="h-screen overflow-y-auto snap-y snap-mandatory scroll-smooth">

                <Section id="hero" className="bg-slate-50">
                    <Carousel>
                        <CarouselContent>
                            <CarouselItem>
                                <Image src={pic1} alt="Ảnh 1" className="w-full h-auto object-cover" />
                            </CarouselItem>
                            <CarouselItem>
                                <Image src={pic2} alt="Ảnh 2" className="w-full h-auto object-cover" />
                            </CarouselItem>
                            <CarouselItem>
                                <Image src={pic3} alt="Ảnh 3" className="w-full h-auto object-cover" />
                            </CarouselItem>
                        </CarouselContent>
                        <CarouselPrevious />
                        <CarouselNext />
                    </Carousel>
                </Section>

                <Section id="section-1" className="bg-white flex items-center justify-center py-20">
                    <div className="container mx-auto px-6 flex flex-col md:flex-row items-center gap-12">
                        <div className="flex-1 space-y-6">
                            <h3 className="text-[#5B0019] font-bold uppercase tracking-widest text-sm">
                                CÁC SINH VIÊN
                            </h3>
                            <h2 className="text-4xl md:text-5xl font-extrabold text-[#1a1a1a] leading-tight">
                                Các Sinh viên Kinh nghiệm
                            </h2>
                            <p className="text-gray-600 text-lg leading-relaxed max-w-xl">
                                Lakeside là một cộng đồng học tập sôi động, nơi học sinh được khuyến khích khám phá đam mê của họ,
                                phát triển kỹ năng lãnh đạo và xây dựng những mối quan hệ bền chặt. Chúng tôi tin rằng giáo dục
                                không chỉ diễn ra trong lớp học mà còn thông qua các hoạt động ngoại khóa, dự án cộng đồng và giao lưu văn hóa.
                            </p>
                            <button className="px-8 py-3 border-2 border-[#5B0019] text-[#5B0019] font-semibold rounded-md hover:bg-[#5B0019] hover:text-white transition-all uppercase text-sm tracking-wider">
                                Tìm hiểu thêm
                            </button>
                        </div>

                        <div className="flex-1 w-full">
                            <div className="relative rounded-2xl overflow-hidden shadow-2xl transform hover:scale-[1.02] transition-transform duration-300">
                                <Image
                                    src={experience}
                                    alt="Sinh viên tại Lakeside"
                                    className="w-full h-full object-cover aspect-4/3"
                                />
                            </div>
                        </div>
                    </div>
                </Section>

                <Section id="section-2" className="bg-white py-16 px-8 md:px-20">
                    <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-12">
                        <div className="w-full md:w-1/2">
                            <Image
                                src={study}
                                alt="Trường học"
                                className="rounded-2xl shadow-lg w-full h-100 object-cover"
                            />
                        </div>

                        <div className="w-full md:w-1/2 space-y-6 text-left">
                            <header>
                                <p className="text-sm font-semibold text-red-800 uppercase tracking-widest mb-2">
                                    Học Tập
                                </p>
                                <h2 className="text-5xl font-extrabold text-slate-900 leading-tight">
                                    Học tập Học thuật
                                </h2>
                            </header>

                            <p className="text-gray-600 text-lg leading-relaxed">
                                Chương trình học tập của chúng tôi được thiết kế để thách thức và truyền cảm hứng cho học sinh.
                                Với đội ngũ giáo viên giàu kinh nghiệm và tận tâm, chúng tôi cung cấp một môi trường học tập
                                hỗ trợ và khuyến khích tư duy phản biện, sáng tạo và độc lập.
                            </p>

                            <button className="mt-4 px-8 py-3 border-2 border-orange-300 text-orange-400 font-bold rounded-sm hover:bg-orange-50 transition-colors uppercase tracking-wide">
                                Khám phá chương trình
                            </button>
                        </div>
                    </div>
                </Section>

                <Section id="section-3" className="py-16 px-8 md:px-20 bg-white">
                    <div className="flex flex-col md:flex-row items-center gap-12 max-w-7xl mx-auto">
                        <div className="flex-1 space-y-6">
                            <p className="text-sm font-bold uppercase tracking-widest text-red-800">
                                Athletics
                            </p>
                            <h2 className="text-5xl font-extrabold text-slate-900 leading-tight">
                                Thể thao & Vận động
                            </h2>
                            <p className="text-gray-600 leading-relaxed text-lg">
                                Chương trình thể thao của Lakeside phát triển tinh thần đồng đội, kỷ luật
                                và sự kiên trì. Với nhiều môn thể thao khác nhau từ bóng rổ, bơi lội đến
                                bóng đá, học sinh có cơ hội phát triển kỹ năng thể chất và tinh thần cạnh
                                tranh lành mạnh.
                            </p>
                            <button className="mt-4 px-8 py-3 border-2 border-amber-600 text-amber-700 font-semibold uppercase tracking-wider hover:bg-amber-600 hover:text-white transition-all duration-300">
                                Xem các đội thể thao
                            </button>
                        </div>

                        <div className="flex-1 relative">
                            <Image
                                src={sport}
                                alt="Thể thao tại Lakeside"
                                className="w-full h-full object-cover rounded-2xl shadow-lg transform hover:scale-[1.02] transition-transform duration-300 aspect-4/3"
                            />
                            <div className="absolute -right-8 top-1/2 transform -translate-y-1/2 flex flex-col gap-3">
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <div key={i} className={`w-2 h-2 rounded-full ${i === 3 ? 'bg-red-800' : 'bg-gray-300'}`} />
                                ))}
                            </div>
                        </div>
                    </div>
                </Section>

                <Section id="section-4" className="bg-white flex items-center justify-center py-20">
                    <div className="container mx-auto px-6 flex flex-col md:flex-row-reverse items-center gap-12">
                        <div className="flex-1 space-y-6">
                            <h3 className="text-[#5B0019] font-bold uppercase tracking-widest text-sm">
                                NGHỆ THUẬT
                            </h3>
                            <h2 className="text-4xl md:text-5xl font-extrabold text-[#1a1a1a] leading-tight">
                                Nghệ thuật & Sáng tạo
                            </h2>
                            <p className="text-gray-600 text-lg leading-relaxed max-w-xl">
                                Lakeside khuyến khích sự sáng tạo và biểu đạt cá nhân thông qua các chương trình
                                nghệ thuật đa dạng bao gồm âm nhạc, hội họa, kịch nghệ và nhiều lĩnh vực khác.
                                Học sinh được tự do khám phá và phát triển tài năng nghệ thuật của mình trong
                                môi trường hỗ trợ và chuyên nghiệp.
                            </p>
                            <button className="px-8 py-3 border-2 border-[#b58e58] text-[#b58e58] font-semibold rounded-md hover:bg-[#b58e58] hover:text-white transition-all uppercase text-sm tracking-wider">
                                Khám phá nghệ thuật
                            </button>
                        </div>

                        <div className="flex-1 w-full">
                            <div className="relative rounded-2xl overflow-hidden shadow-xl transform hover:scale-[1.02] transition-transform duration-300">
                                <Image
                                    src={art}
                                    alt="Nghệ thuật tại Lakeside"
                                    className="w-full h-full object-cover aspect-4/3"
                                />
                            </div>
                        </div>
                    </div>
                </Section>

            </main>
        </div>
    );
}
