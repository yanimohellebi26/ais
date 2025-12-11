import React from "react";
import { DayPicker, DateRange } from "react-day-picker";
import "react-day-picker/dist/style.css";
import { format } from "date-fns";

type DatePickerProps = {
    mode?: "single" | "range";
    className?: string;
    selected?: Date | DateRange | undefined;
    onSelect?: (value: Date | DateRange | undefined) => void;
};

const DatePicker: React.FC<DatePickerProps> = ({
                                                   mode = "single",
                                                   className = "",
                                                   selected,
                                                   onSelect,
                                               }) => {
    const handleSelect = (value: Date | DateRange | undefined) => {
        onSelect?.(value);
    };

    let footerText = "";
    if (mode === "range") {
        const range = selected as DateRange | undefined;
        if (range?.from && range?.to) {
            footerText = `From ${format(range.from, "yyyy-MM-dd")} to ${format(
                range.to,
                "yyyy-MM-dd"
            )}`;
        } else {
            footerText = "Choose date range";
        }
    } else if (selected instanceof Date) {
        footerText = `Selected date: ${format(selected, "yyyy-MM-dd")}`;
    } else {
        footerText = "Choose date";
    }

    const footer = <p className="text-sm text-base-content/70 mt-2">{footerText}</p>;

    return (
        <div className={`bg-white rounded-2xl inline-block ${className}`}>
            {mode === "range" ? (
                <DayPicker
                    className="scale-90 [&_*]:text-sm [&_table]:text-sm [&_table]:leading-tight"
                    mode="range"
                    selected={selected as DateRange | undefined}
                    onSelect={handleSelect as (range: DateRange | undefined) => void}
                    footer={footer}
                />
            ) : (
                <DayPicker
                    className="scale-90 [&_*]:text-sm [&_table]:text-sm [&_table]:leading-tight"
                    mode="single"
                    selected={selected as Date | undefined}
                    onSelect={handleSelect as (date: Date | undefined) => void}
                    footer={footer}
                />
            )}
        </div>
    );
};

export default DatePicker;
