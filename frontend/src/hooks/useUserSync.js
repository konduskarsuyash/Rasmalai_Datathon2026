import { useUser } from "@clerk/clerk-react";
import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useUserSync() {
  const { user, isSignedIn } = useUser();
  const [isSynced, setIsSynced] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const syncUser = async () => {
      if (!isSignedIn || !user || isSynced) return;

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
          setIsSynced(true);
          console.log("User synced successfully");
        } else {
          const errorData = await response.json();
          console.error("Failed to sync user:", errorData);
          setError(errorData.detail || "Failed to sync user");
        }
      } catch (err) {
        console.error("Error syncing user:", err);
        setError(err.message);
      }
    };

    syncUser();
  }, [user, isSignedIn, isSynced]);

  return { isSynced, error };
}
