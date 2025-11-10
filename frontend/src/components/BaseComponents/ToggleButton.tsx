import { useState, ReactNode } from "react";

interface ToggleButtonProps {
    onIcon: ReactNode;
    offIcon: ReactNode;
    onToggle?: () => void;
    className?: string;
}

const ToggleButton : React.FC<ToggleButtonProps> = ({
                                                        onIcon,
                                                        offIcon,
                                                        onToggle,
                                                        className,
                                                    }) => {
    const [active, setActive] = useState(false);

    const handleClick = () => {
        setActive(!active);
        onToggle?.();
    };

    return (

        <div className={className}>
            <label className="btn btn-circle swap swap-rotate hover:scale-110 transition-transform duration-150 ease-in-out">
                <input type="checkbox" onClick={handleClick}/>

                <span className="swap-off fill-current flex items-center justify-center">
          {offIcon}
        </span>

                <span className="swap-on fill-current flex items-center justify-center">
          {onIcon}
        </span>
            </label>

        </div>
    );
}

export default ToggleButton;
