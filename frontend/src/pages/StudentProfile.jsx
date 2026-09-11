import { useEffect, useState } from "react";
import api from "../api/axios";
import ResumeUpload from "../components/ResumeUpload";

export default function StudentProfile() {
  const [profile, setProfile] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [profileRes, readinessRes] = await Promise.all([
          api.get("/students/me"),
          api.get("/students/me/readiness"),
        ]);
        setProfile(profileRes.data);
        setReadiness(readinessRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load data");
      }
    };
    fetchData();
  }, []);

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  if (!profile || !readiness) {
    return <p>Loading...</p>;
  }

  const bandColors = {
    "Not Ready": "bg-red-200",
    Developing: "bg-yellow-200",
    Ready: "bg-green-200",
    "Highly Employable": "bg-blue-200",
  };

  return (
    <div className="max-w-2xl mx-auto mt-8 p-4 border rounded">
      <h2 className="text-2xl mb-4">Student Profile</h2>
      <p><strong>Name:</strong> {profile.name}</p>
      <p><strong>Branch:</strong> {profile.branch}</p>
      <p><strong>CGPA:</strong> {profile.cgpa}</p>

      <h3 className="text-xl mt-4 mb-2">Readiness Score</h3>
      <div className={`p-2 rounded ${bandColors[readiness.band] || "bg-gray-200"}`}>
        <p className="font-bold">{readiness.band}</p>
        <p>Score: {readiness.score.toFixed(1)} / 100</p>
        <p>{readiness.explanation}</p>
      </div>

      <h4 className="mt-4 mb-2 font-semibold">Breakdown</h4>
      <ul className="list-disc list-inside">
        {Object.entries(readiness.breakdown).map(([k, v]) => (
          <li key={k}>{k}: {v.toFixed(1)}</li>
        ))}
      </ul>

      <h4 className="mt-4 mb-2 font-semibold">Upload Resume</h4>
      <ResumeUpload />
    </div>
  );
}
