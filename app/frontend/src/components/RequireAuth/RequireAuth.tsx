import { ReactNode, useEffect } from "react";
import { useMsal } from "@azure/msal-react";
import { useLogin, checkLoggedIn } from "../../authConfig";

interface RequireAuthProps {
    children: ReactNode;
}

const RequireAuth = ({ children }: RequireAuthProps) => {
    const { instance } = useMsal();

    useEffect(() => {
        if (!useLogin) {
            return;
        }
        checkLoggedIn(instance).then(isLogged => {
            if (!isLogged) {
                instance.loginRedirect().catch(e => {
                    console.error("loginRedirect failed", e);
                });
            }
        });
    }, [instance]);

    return <>{children}</>;
};

export default RequireAuth;
