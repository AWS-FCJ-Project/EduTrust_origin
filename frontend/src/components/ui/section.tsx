import * as React from "react"
import { cn } from "@/lib/utils"

interface SectionProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode
    fullHeight?: boolean
}

const Section = React.forwardRef<HTMLDivElement, SectionProps>(
    ({ className, children, fullHeight = true, ...props }, ref) => {
        return (
            <section
                ref={ref}
                className={cn(
                    "w-full flex items-center justify-center relative",
                    fullHeight && "h-screen snap-start snap-always",
                    className
                )}
                {...props}
            >
                {children}
            </section>
        )
    }
)
Section.displayName = "Section"

export { Section }