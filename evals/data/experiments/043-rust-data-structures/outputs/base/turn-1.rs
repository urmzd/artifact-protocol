impl<K: Eq + Hash + Clone, V> LruCache<K, V> {
    pub fn get_or_insert<F>(&mut self, key: K, f: F) -> &V
    where
        F: FnOnce() -> V,
    {
        if !self.map.contains_key(&key) {
            let val = f();
            self.put(key.clone(), val);
        }
        self.get(&key).unwrap()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lru_get_or_insert() {
        let mut lru = LruCache::new(2);
        let val = lru.get_or_insert(1, || "computed".to_string());
        assert_eq!(val, "computed");
        
        let val2 = lru.get_or_insert(1, || "new".to_string());
        assert_eq!(val2, "computed");
        assert_eq!(lru.len(), 1);
    }
}