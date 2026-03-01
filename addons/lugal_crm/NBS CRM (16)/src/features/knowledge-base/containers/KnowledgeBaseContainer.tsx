import { useKnowledge } from '../hooks/useKnowledge';
import { KnowledgeBase } from '../../../app/components/knowledge-base/knowledge-base';

export function KnowledgeBaseContainer() {
  const {
    articles, circulars, selectedArticle, isLoading, error,
    setSelected, setSearchQuery, setCategory, openArticle, createArticle,
  } = useKnowledge();

  return (
    <KnowledgeBase
      articles={articles as never}
      circulars={circulars as never}
      selectedArticle={selectedArticle as never}
      isLoading={isLoading}
      error={error}
      onSearch={setSearchQuery}
      onCategoryChange={setCategory}
      onSelectArticle={(id) => openArticle(id)}
      onCloseArticle={() => setSelected(null)}
      onCreateArticle={createArticle as never}
    />
  );
}
