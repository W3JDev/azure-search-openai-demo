import { useEffect, useState } from "react";
import { useMsal } from "@azure/msal-react";
import { getToken } from "../../authConfig";
import { getJson } from "../../api";

interface Report {
    content: string;
}

const ReportViewer = () => {
    const { instance } = useMsal();
    const [report, setReport] = useState<Report | null>(null);

    useEffect(() => {
        const load = async () => {
            const token = await getToken(instance);
            try {
                const data = await getJson<Report>("/report", token);
                setReport(data);
            } catch (e) {
                console.error(e);
            }
        };
        load();
    }, [instance]);

    return <pre>{report ? report.content : "No report"}</pre>;
};

export default ReportViewer;
