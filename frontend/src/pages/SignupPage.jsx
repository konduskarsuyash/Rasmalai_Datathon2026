import { SignUp } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

function SignupPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-950 to-gray-900 text-white flex items-center justify-center p-6">
      <div className="max-w-md w-full">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <Link
            to="/"
            className="text-4xl font-bold text-red-400 hover:text-red-300 transition"
          >
            FinNet
          </Link>
          <p className="text-gray-400 mt-2">
            Join the financial network revolution
          </p>
        </div>

        {/* Clerk Sign Up Component */}
        <div className="flex justify-center">
          <SignUp
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "bg-gray-800/50 backdrop-blur-sm border border-red-900/30 shadow-xl",
                headerTitle: "text-white",
                headerSubtitle: "text-gray-400",
                socialButtonsBlockButton:
                  "bg-gray-700 hover:bg-gray-600 text-white border-gray-600",
                socialButtonsBlockButtonText: "text-white",
                formButtonPrimary: "bg-red-600 hover:bg-red-700 text-white",
                formFieldLabel: "text-gray-300",
                formFieldInput: "bg-gray-700/50 border-gray-600 text-white",
                footerActionLink: "text-red-400 hover:text-red-300",
                identityPreviewText: "text-white",
                identityPreviewEditButton: "text-red-400",
              },
            }}
            routing="path"
            path="/signup"
            signInUrl="/login"
            redirectUrl="/playground"
          />
        </div>

        {/* Back to Home */}
        <div className="text-center mt-6">
          <Link to="/" className="text-gray-400 hover:text-white transition">
            ← Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;
