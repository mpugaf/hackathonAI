import { useCallback, useEffect, useState } from 'react';
import { listRequirements } from '../api/requirements';

export default function useRequirements() {
  const [requirements, setRequirements] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setRequirements(await listRequirements({ skip: 0, limit: 20 }));
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { requirements, isLoading, error, refresh };
}
