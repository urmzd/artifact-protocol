<aap:target id="rust-data-structures">
use std::collections::{HashMap, VecDeque};
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

<aap:target id="lru-cache">    pub fn get(&mut self, key: &K) -> Option<&V> {
        self.map.get(key).map(|(v, _)| v)
    }

    pub fn get_or_insert<F>(&mut self, key: K, f: F) -> &V
    where
        F: FnOnce() -> V,
        K: Clone,
    {
        if self.map.contains_key(&key) {
            return self.get(&key).unwrap();
        }
        let value = f();
        self.put(key.clone(), value);
        self.get(&key).unwrap()
    }

    pub fn put(&mut self, key: K, value: V) {</aap:target>

<aap:target id="trie">
#[derive(Default)]
pub struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end: bool,
}

pub struct Trie {
    root: TrieNode,
}

impl Trie {
    pub fn new() -> Self { Self { root: TrieNode::default() } }
    pub fn insert(&mut self, word: &str) {
        let mut curr = &mut self.root;
        for c in word.chars() {
            curr = curr.children.entry(c).or_insert(TrieNode::default());
        }
        curr.is_end = true;
    }
    
    pub fn search(&self, word: &str) -> bool {
        self.search_recursive(&self.root, word)
    }

    fn search_recursive(&self, node: &TrieNode, word: &str) -> bool {
        if word.is_empty() {
            return node.is_end;
        }

        let first = word.chars().next().unwrap();
        let remaining = &word[first.len_utf8()..];

        match first {
            '?' => {
                for child in node.children.values() {
                    if self.search_recursive(child, remaining) {
                        return true;
                    }
                }
            }
            '*' => {
                if self.search_recursive(node, remaining) {
                    return true;
                }
                for child in node.children.values() {
                    if self.search_recursive(child, word) {
                        return true;
                    }
                }
            }
            c => {
                if let Some(child) = node.children.get(&c) {
                    return self.search_recursive(child, remaining);
                }
            }
        }
        false
    }
}
</aap:target>

<aap:target id="bloom-filter">
pub struct BloomFilter {
    bits: Vec<bool>,
    num_hashes: usize,
    size: usize,
}

impl BloomFilter {
    pub fn new(expected_elements: usize, false_positive_rate: f64) -> Self {
        let size = (-(expected_elements as f64) * false_positive_rate.ln() / (2.0f64.ln().powi(2))) as usize;
        let num_hashes = ((size as f64 / expected_elements as f64) * 2.0f64.ln()) as usize;
        Self { bits: vec![false; size], num_hashes, size }
    }
    pub fn insert<T: Hash>(&mut self, item: &T) {
        for i in 0..self.num_hashes {
            let mut h = DefaultHasher::new();
            item.hash(&mut h);
            i.hash(&mut h);
            let idx = (h.finish() as usize) % self.size;
            self.bits[idx] = true;
        }
    }
}
</aap:target>

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_trie() {
        let mut t = Trie::new();
        t.insert("rust");
        assert!(t.search("rust"));
        assert!(t.search("r?st"));
        assert!(t.search("r*t"));
        assert!(!t.search("ru"));
    }

    #[test]
    fn test_bloom() {
        let mut bf = BloomFilter::new(100, 0.01);
        bf.insert(&"test");
        // probabilistic check
    }
}
</aap:target>
