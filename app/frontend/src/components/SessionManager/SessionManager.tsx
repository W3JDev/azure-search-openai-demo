import { useEffect } from "react";
import { useMsal } from "@azure/msal-react";
import { getToken } from "../../authConfig";

const SessionManager = () => {
    const { instance } = useMsal();

    useEffect(() => {
        // Prime token retrieval to manage session state
        getToken(instance).catch(err => {
            console.error("Token retrieval failed", err);
        });
    }, [instance]);

    return <div>Session Manager</div>;
};

export default SessionManager;
