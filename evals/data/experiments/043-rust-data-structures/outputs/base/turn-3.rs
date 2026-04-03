struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end: bool,
    count: usize,
}

impl TrieNode {
    fn new() -> Self {
        Self { children: HashMap::new(), is_end: false, count: 0 }
    }
}

impl Trie {
    pub fn new() -> Self {
        Self { root: TrieNode::new() }
    }

    pub fn insert(&mut self, word: &str) {
        let mut curr = &mut self.root;
        curr.count += 1;
        for c in word.chars() {
            curr = curr.children.entry(c).or_insert(TrieNode::new());
            curr.count += 1;
        }
        curr.is_end = true;
    }

    pub fn count_prefix(&self, prefix: &str) -> usize {
        let mut curr = &self.root;
        for c in prefix.chars() {
            match curr.children.get(&c) {
                Some(node) => curr = node,
                None => return 0,
            }
        }
        curr.count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_trie_count_prefix() {
        let mut t = Trie::new();
        t.insert("apple");
        t.insert("apply");
        t.insert("app");
        t.insert("bat");
        
        assert_eq!(t.count_prefix("app"), 3);
        assert_eq!(t.count_prefix("appl"), 2);
        assert_eq!(t.count_prefix("bat"), 1);
        assert_eq!(t.count_prefix("z"), 0);
    }
}