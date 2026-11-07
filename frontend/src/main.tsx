import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";

const params = new URLSearchParams(window.location.search);
const redirectPath = params.get("redirect");
if (redirectPath) {
  const nextPath = decodeURIComponent(redirectPath);
  window.history.replaceState(null, "", nextPath);
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
