import { useState } from "react";
import api from "../api/axios";

export default function ResumeUpload() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setStatus("Select a PDF file first");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);
    try {
      await api.post("/students/me/resume", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus("Resume uploaded successfully");
    } catch (err) {
      setStatus(err.response?.data?.detail || "Upload failed");
    }
  };

  return (
    <form onSubmit={handleUpload} className="flex flex-col gap-2">
      <input type="file" accept=".pdf" onChange={handleFileChange} />
      <button type="submit" className="bg-blue-600 text-white py-1 rounded">Upload</button>
      {status && <p>{status}</p>}
    </form>
  );
}
