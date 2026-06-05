import { useCallback, useEffect, useState } from 'react';
import { getRequirement } from '../api/requirements';

export default function useRequirementDetail(id) {
  const [requirement, setRequirement] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setRequirement(await getRequirement(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { requirement, setRequirement, isLoading, error, refresh };
}
