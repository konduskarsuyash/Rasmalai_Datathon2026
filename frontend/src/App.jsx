import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  RedirectToSignIn,
} from "@clerk/clerk-react";
import "./App.css";
import HeroPage from "./pages/HeroPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import FinancialNetworkPlayground from "./components/FinancialNetworkPlayground";
import ErrorBoundary from "./components/ErrorBoundary";
import { UserSyncWrapper } from "./components/UserSyncWrapper";

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

// Protected Route Component
function ProtectedRoute({ children }) {
  return (
    <>
      <SignedIn>
        <UserSyncWrapper>{children}</UserSyncWrapper>
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
}

function App() {
  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      <Router>
        <Routes>
          <Route path="/" element={<HeroPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route
            path="/playground"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <div className="min-h-screen bg-gray-900">
                    <FinancialNetworkPlayground />
                  </div>
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </ClerkProvider>
  );
}

export default App;
