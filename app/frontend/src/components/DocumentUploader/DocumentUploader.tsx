import { useState, ChangeEvent } from "react";
import { useMsal } from "@azure/msal-react";
import { getToken } from "../../authConfig";
import { postForm, SimpleAPIResponse } from "../../api";

const DocumentUploader = () => {
    const { instance } = useMsal();
    const [file, setFile] = useState<File | null>(null);
    const [message, setMessage] = useState<string>("");

    const onChange = (e: ChangeEvent<HTMLInputElement>) => {
        setFile(e.target.files ? e.target.files[0] : null);
    };

    const upload = async () => {
        if (!file) return;
        const token = await getToken(instance);
        const form = new FormData();
        form.append("file", file);
        try {
            const res = await postForm<SimpleAPIResponse>("/upload", form, token);
            setMessage(res.message ?? "Uploaded");
        } catch (e: any) {
            setMessage(e.message);
        }
    };

    return (
        <div>
            <input type="file" onChange={onChange} />
            <button onClick={upload} disabled={!file}>Upload</button>
            {message && <p>{message}</p>}
        </div>
    );
};

export default DocumentUploader;
