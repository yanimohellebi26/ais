import { useState, ReactNode } from "react";

interface ToggleButtonProps {
  onIcon: ReactNode;
  offIcon: ReactNode;
  onToggle?: () => void;
}

const ToggleButton : React.FC<ToggleButtonProps> = ({
  onIcon,
  offIcon,
  onToggle
}) => {
  const [active, setActive] = useState(false);

  const handleClick = () => {
    setActive(!active);
    onToggle?.();
  };

  return (

    <div>
      <label className="btn btn-circle btn-neutral swap swap-rotate">
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
