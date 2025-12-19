import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  InputAdornment,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSearchStore } from '../../stores/searchStore';

export default function SearchPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [query, setQuery] = useState('');
  const { results, isLoading, globalSearch, took_ms } = useSearchStore();
  const safeResults = Array.isArray(results) ? results : [];

  useEffect(() => {
    const sp = new URLSearchParams(location.search || '');
    const q = sp.get('q') || '';
    if (q.trim()) {
      setQuery(q);
      globalSearch(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {t('search.title')}
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleSearch}>
          <TextField
            fullWidth
            placeholder={t('search.placeholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <Button
                  type="submit"
                  variant="contained"
                  disabled={isLoading || !query.trim()}
                >
                  {isLoading ? t('search.searching') : t('search.search')}
                </Button>
              ),
            }}
          />
        </form>
      </Paper>

      {safeResults.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              {t('search.results')} ({safeResults.length})
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {t('search.took', { ms: took_ms })}
            </Typography>
          </Box>

          <List>
            {safeResults.map((result: any) => (
              <ListItem
                key={result.document_id ?? result.id}
                button
                onClick={() => {
                  if (result.entity_type === 'folder') navigate(`/folders/${result.id}`);
                  else navigate(`/documents/${result.document_id ?? result.id}`);
                }}
                sx={{
                  border: '1px solid #e0e0e0',
                  borderRadius: 1,
                  mb: 1,
                }}
              >
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1">{result.title || result.name || '-'}</Typography>
                      <Chip label={result.entity_type || 'document'} size="small" />
                      {result.barcode && <Chip label={result.barcode} size="small" />}
                      {typeof result.score === 'number' && (
                        <Chip label={`Score: ${result.score.toFixed(2)}`} size="small" color="primary" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        {(result.department || result.department_name || '-')}{' '}
                        {result.document_type || result.document_type_name ? `• ${result.document_type || result.document_type_name} ` : ''}
                        {result.uploader || result.uploader_name ? `• ${result.uploader || result.uploader_name}` : ''}
                      </Typography>
                      {result.highlights && (
                        <Box mt={1}>
                          {result.highlights.content && (
                            <Typography
                              variant="body2"
                              dangerouslySetInnerHTML={{
                                __html: result.highlights.content[0] || '',
                              }}
                            />
                          )}
                        </Box>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {!isLoading && query && safeResults.length === 0 && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="textSecondary">{t('search.noResults')}</Typography>
        </Paper>
      )}
    </Box>
  );
}


