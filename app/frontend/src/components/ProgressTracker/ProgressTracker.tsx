interface ProgressTrackerProps {
    progress: number; // value between 0 and 1
}

const ProgressTracker = ({ progress }: ProgressTrackerProps) => {
    return <progress value={progress} max={1} />;
};

export default ProgressTracker;
