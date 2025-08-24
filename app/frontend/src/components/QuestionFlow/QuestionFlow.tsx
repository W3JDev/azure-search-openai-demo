import { useState } from "react";

const QuestionFlow = () => {
    const [step, setStep] = useState(0);
    const next = () => setStep(s => s + 1);

    return (
        <div>
            <p>Question Flow Step: {step}</p>
            <button onClick={next}>Next</button>
        </div>
    );
};

export default QuestionFlow;
