import { useState, useEffect } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";

export default function RecruiterDashboard() {
  const { token } = useAuth();
  const [job, setJob] = useState({
    title: "",
    ctc: "",
    min_cgpa: "",
    eligible_branches: "",
    required_skills: "",
  });
  const [createdJobId, setCreatedJobId] = useState(null);
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setJob({ ...job, [e.target.name]: e.target.value });
  };

  const createJob = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const response = await api.post("/recruiter/jobs", {
        title: job.title,
        ctc: parseFloat(job.ctc),
        min_cgpa: parseFloat(job.min_cgpa),
        eligible_branches: job.eligible_branches,
        required_skills: job.required_skills,
      });
      setCreatedJobId(response.data.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Job creation failed");
    }
  };

  const runMatch = async () => {
    if (!createdJobId) return;
    setError("");
    try {
      const res = await api.get(`/recruiter/jobs/${createdJobId}/match`);
      setMatches(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Matching failed");
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-8 p-4 border rounded">
      <h2 className="text-2xl mb-4">Recruiter Dashboard</h2>
      {error && <p className="text-red-600">{error}</p>}
      <form onSubmit={createJob} className="flex flex-col gap-2 mb-4">
        <input name="title" placeholder="Job Title" value={job.title} onChange={handleChange} required className="p-2 border rounded" />
        <input name="ctc" type="number" step="0.01" placeholder="CTC (e.g., 12.5)" value={job.ctc} onChange={handleChange} required className="p-2 border rounded" />
        <input name="min_cgpa" type="number" step="0.01" placeholder="Min CGPA" value={job.min_cgpa} onChange={handleChange} required className="p-2 border rounded" />
        <input name="eligible_branches" placeholder="Eligible Branches (comma‑separated)" value={job.eligible_branches} onChange={handleChange} required className="p-2 border rounded" />
        <input name="required_skills" placeholder="Required Skills (comma‑separated)" value={job.required_skills} onChange={handleChange} required className="p-2 border rounded" />
        <button type="submit" className="bg-blue-600 text-white py-1 rounded">Create Job</button>
      </form>
      {createdJobId && (
        <div className="mb-4">
          <p>Job created with ID: {createdJobId}</p>
          <button onClick={runMatch} className="bg-green-600 text-white py-1 rounded">Run Matching</button>
        </div>
      )}
      {matches.length > 0 && (
        <div>
          <h3 className="text-xl mb-2">Match Results</h3>
          <ul className="list-disc list-inside">
            {matches.map((m) => (
              <li key={m.student_id}>
                {m.name} – Score: {m.score.toFixed(1)} (Skill: {m.breakdown.skill_sum}, Readiness: {m.breakdown.readiness})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
