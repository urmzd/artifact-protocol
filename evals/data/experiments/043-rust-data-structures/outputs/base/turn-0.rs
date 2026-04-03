use std::collections::{HashMap, VecDeque};
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;
use std::rc::Rc;
use std::cell::RefCell;

pub struct LruCache<K, V> {
    capacity: usize,
    map: HashMap<K, (V, usize)>,
    order: VecDeque<K>,
    timestamp: usize,
}

impl<K: Eq + Hash + Clone, V> LruCache<K, V> {
    pub fn new(capacity: usize) -> Self {
        Self { capacity, map: HashMap::with_capacity(capacity), order: VecDeque::with_capacity(capacity), timestamp: 0 }
    }

    pub fn get(&mut self, key: &K) -> Option<&V> {
        if self.map.contains_key(key) {
            self.timestamp += 1;
            self.map.get_mut(key).map(|v| { v.1 = self.timestamp; &v.0 })
        } else { None }
    }

    pub fn put(&mut self, key: K, value: V) {
        if self.map.len() >= self.capacity && !self.map.contains_key(&key) {
            let oldest = self.order.pop_front().unwrap();
            self.map.remove(&oldest);
        }
        self.timestamp += 1;
        self.map.insert(key.clone(), (value, self.timestamp));
        self.order.push_back(key);
    }

    pub fn remove(&mut self, key: &K) -> Option<V> {
        self.order.retain(|k| k != key);
        self.map.remove(key).map(|v| v.0)
    }

    pub fn len(&self) -> usize { self.map.len() }
    pub fn clear(&mut self) { self.map.clear(); self.order.clear(); }
}

#[derive(Default)]
struct TrieNode {
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
            curr = curr.children.entry(c).or_default();
        }
        curr.is_end = true;
    }

    pub fn search(&self, word: &str) -> bool {
        self.find(word).map(|n| n.is_end).unwrap_or(false)
    }

    pub fn starts_with(&self, prefix: &str) -> bool {
        self.find(prefix).is_some()
    }

    fn find(&self, s: &str) -> Option<&TrieNode> {
        let mut curr = &self.root;
        for c in s.chars() {
            curr = curr.children.get(&c)?;
        }
        Some(curr)
    }

    pub fn autocomplete(&self, prefix: &str) -> Vec<String> {
        let mut results = Vec::new();
        if let Some(node) = self.find(prefix) {
            self.dfs(node, &mut prefix.to_string(), &mut results);
        }
        results
    }

    fn dfs(&self, node: &TrieNode, path: &mut String, results: &mut Vec<String>) {
        if node.is_end { results.push(path.clone()); }
        for (c, next) in &node.children {
            path.push(*c);
            self.dfs(next, path, results);
            path.pop();
        }
    }
}

pub struct BloomFilter {
    bits: Vec<bool>,
    hashes: usize,
}

impl BloomFilter {
    pub fn new(n: usize, p: f64) -> Self {
        let m = (-(n as f64) * p.ln() / (2.0f64.ln().powi(2))).ceil() as usize;
        let k = ((m as f64 / n as f64) * 2.0f64.ln()).round() as usize;
        Self { bits: vec![false; m], hashes: k }
    }

    fn get_indices<T: Hash>(&self, item: &T) -> Vec<usize> {
        (0..self.hashes).map(|i| {
            let mut s = DefaultHasher::new();
            item.hash(&mut s);
            (i as u64).hash(&mut s);
            (s.finish() as usize) % self.bits.len()
        }).collect()
    }

    pub fn insert<T: Hash>(&mut self, item: &T) {
        for idx in self.get_indices(item) { self.bits[idx] = true; }
    }

    pub fn contains<T: Hash>(&self, item: &T) -> bool {
        self.get_indices(item).iter().all(|&idx| self.bits[idx])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lru() {
        let mut lru = LruCache::new(2);
        lru.put(1, "a");
        lru.put(2, "b");
        assert_eq!(lru.get(&1), Some(&"a"));
        lru.put(3, "c");
        assert_eq!(lru.get(&2), None);
    }

    #[test]
    fn test_trie() {
        let mut t = Trie::new();
        t.insert("apple");
        assert!(t.search("apple"));
        assert!(t.starts_with("app"));
        assert_eq!(t.autocomplete("app"), vec!["apple"]);
    }

    #[test]
    fn test_bloom() {
        let mut bf = BloomFilter::new(100, 0.01);
        bf.insert(&"hello");
        assert!(bf.contains(&"hello"));
        assert!(!bf.contains(&"world"));
    }
}