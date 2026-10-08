import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { App } from "./App";
import { Home } from "./pages/Home";
import { PassportPage } from "./pages/Passport";
import { Sources } from "./pages/Sources";
import { Corpus } from "./pages/Corpus";
import { NotFound } from "./pages/NotFound";
import "./index.css";

const qc = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, refetchOnWindowFocus: false },
  },
});

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "isin/:isin", element: <PassportPage /> },
      { path: "sources", element: <Sources /> },
      { path: "corpus", element: <Corpus /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={qc}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
