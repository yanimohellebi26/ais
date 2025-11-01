interface Props {
    label: string;
    done: boolean;
    active: boolean;
    isLast?: boolean;
    error: boolean;
}

const Step: React.FC<Props> = ({ label, done, active, isLast,error }) => (
    <div className="flex gap-3">
        <div className="flex flex-col items-center">
            <div
                className={`
        w-5 h-5 rounded-full border-2
        ${done ? "border-success bg-success" : "border-base"}
        ${(active && !error && !done)  ? "border-primary animate-ping bg-primary/30"  : ""}
        ${error ? `border-error/30 bg-error` : ""}
       
      `}
            />
            {!isLast && (
                <div className={`
                w-1 h-4 
                ${done ? "bg-success/60" : "bg-base-content"}
                `}></div>
            )}
        </div>
        <span className={`  ${done ? "text-success " : error ? "text-error font-semibold" : active ? "text-primary font-semibold" : "text-base-content/70"}`}>
        {label}
        </span>
    </div>
);

export default Step;
