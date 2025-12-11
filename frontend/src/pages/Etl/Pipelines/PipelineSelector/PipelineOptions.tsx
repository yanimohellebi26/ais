import React from "react";

interface Props {
    continueOnError: boolean;
    useTimer: boolean;
    force: boolean;
    onChangeContinue: (value: boolean) => void;
    onChangeTimer: (value: boolean) => void;
    onChangeForce: (value: boolean) => void;
}

const PipelineOptions: React.FC<Props> = ({
                                              continueOnError,
                                              useTimer,
                                              force,
                                              onChangeContinue,
                                              onChangeTimer,
                                              onChangeForce,
                                          }) => (
    <div className="flex gap-4 items-center">
        <label className="label flex items-center gap-2 cursor-pointer">
            <input
                type="checkbox"
                checked={continueOnError}
                onChange={(e) => onChangeContinue(e.target.checked)}
                className="checkbox"
            />
            <span className="label-text">Continue On Error</span>
        </label>

        <label className="label flex items-center gap-2 cursor-pointer">
            <input
                type="checkbox"
                checked={useTimer}
                onChange={(e) => onChangeTimer(e.target.checked)}
                className="checkbox"
            />
            <span className="label-text">Use timer</span>
        </label>

        <label className="label flex items-center gap-2 cursor-pointer">
            <input
                type="checkbox"
                checked={force}
                onChange={(e) => onChangeForce(e.target.checked)}
                className="checkbox"
            />
            <span className="label-text">⚠️Force</span>
        </label>

    </div>
);

export default PipelineOptions;
