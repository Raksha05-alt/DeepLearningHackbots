import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import CallerApp from "./CallerApp";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <CallerApp />
    </StrictMode>
);
