import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ListView from "./pages/ListView";
import FacilityDetail from "./pages/FacilityDetail";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/list" element={<ListView />} />
        <Route path="/facility/:id" element={<FacilityDetail />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
