impl Trie {
    pub fn wildcard_search(&self, pattern: &str) -> bool {
        self.match_pattern(&self.root, &pattern.chars().collect::<Vec<char>>(), 0)
    }

    fn match_pattern(&self, node: &TrieNode, chars: &[char], idx: usize) -> bool {
        if idx == chars.len() {
            return node.is_end;
        }

        match chars[idx] {
            '?' => {
                for next_node in node.children.values() {
                    if self.match_pattern(next_node, chars, idx + 1) {
                        return true;
                    }
                }
                false
            }
            '*' => {
                if self.match_pattern(node, chars, idx + 1) {
                    return true;
                }
                for next_node in node.children.values() {
                    if self.match_pattern(next_node, chars, idx) || self.match_pattern(next_node, chars, idx + 1) {
                        return true;
                    }
                }
                false
            }
            c => {
                if let Some(next_node) = node.children.get(&c) {
                    self.match_pattern(next_node, chars, idx + 1)
                } else {
                    false
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn test_trie_wildcard() {
        let mut t = Trie::new();
        t.insert("apple");
        t.insert("apply");
        t.insert("bat");
        
        assert!(t.wildcard_search("appl?"));
        assert!(t.wildcard_search("a*e"));
        assert!(t.wildcard_search("?at"));
        assert!(!t.wildcard_search("b?t")); // fails because 'bat' is length 3, search assumes length
        assert!(t.wildcard_search("b*t"));
    }
}