import { useUser } from "@clerk/clerk-react";
import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function UserSyncWrapper({ children }) {
  const { user, isSignedIn, isLoaded } = useUser();
  const [isSynced, setIsSynced] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const syncUser = async () => {
      if (!isLoaded) return;

      if (!isSignedIn || !user) {
        setIsLoading(false);
        return;
      }

      if (isSynced) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/users/sync`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            clerk_id: user.id,
            email: user.primaryEmailAddress?.emailAddress,
            full_name: user.fullName,
            image_url: user.imageUrl,
          }),
        });

        if (response.ok) {
          const userData = await response.json();
          console.log("✅ User synced to MongoDB:", userData);
          setIsSynced(true);
        } else {
          const errorData = await response.json();
          console.error("❌ Failed to sync user:", errorData);
        }
      } catch (err) {
        console.error("❌ Error syncing user:", err);
      } finally {
        setIsLoading(false);
      }
    };

    syncUser();
  }, [user, isSignedIn, isLoaded, isSynced]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-red-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Setting up your account...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
