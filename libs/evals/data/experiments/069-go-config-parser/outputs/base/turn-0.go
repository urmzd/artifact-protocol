package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/go-playground/validator/v10"
	"github.com/knadh/koanf/parsers/yaml"
	"github.com/knadh/koanf/providers/env"
	"github.com/knadh/koanf/providers/file"
	"github.com/knadh/koanf/providers/posixflags"
	"github.com/knadh/koanf/v2"
)

type Config struct {
	Server   ServerConfig   `koanf:"server" validate:"required"`
	Database DatabaseConfig `koanf:"database" validate:"required"`
	Redis    RedisConfig    `koanf:"redis" validate:"required"`
	Logging  LoggingConfig  `koanf:"logging" validate:"required"`
}

type ServerConfig struct {
	Host    string        `koanf:"host" validate:"required,hostname|ip"`
	Port    int           `koanf:"port" validate:"required,gte=1024,lte=65535"`
	Timeout time.Duration `koanf:"timeout" validate:"required"`
}

type DatabaseConfig struct {
	DSN        string `koanf:"dsn" validate:"required,contains=://"`
	PoolSize   int    `koanf:"pool_size" validate:"required,gt=0"`
	Migrations bool   `koanf:"migrations"`
}

type RedisConfig struct {
	Addr     string `koanf:"addr" validate:"required"`
	Password string `koanf:"password"`
	DB       int    `koanf:"db" validate:"gte=0"`
}

type LoggingConfig struct {
	Level  string `koanf:"level" validate:"required,oneof=debug info warn error"`
	Format string `koanf:"format" validate:"required,oneof=json text"`
	Output string `koanf:"output" validate:"required"`
}

var k = koanf.New(".")

func LoadConfig(configPath string) (*Config, error) {
	// 1. Defaults
	defaults := map[string]interface{}{
		"server.host":          "127.0.0.1",
		"server.port":          8080,
		"server.timeout":       "30s",
		"database.pool_size":   10,
		"database.migrations":  true,
		"redis.db":             0,
		"logging.level":        "info",
		"logging.format":       "json",
		"logging.output":       "stdout",
	}
	for k, v := range defaults {
		_ = k.Set(k, v)
	}

	// 2. File
	if _, err := os.Stat(configPath); err == nil {
		if err := k.Load(file.Provider(configPath), yaml.Parser()); err != nil {
			return nil, fmt.Errorf("error loading file: %w", err)
		}
	}

	// 3. Env vars
	if err := k.Load(env.Provider("APP_", ".", func(s string) string {
		return strings.Replace(strings.ToLower(strings.TrimPrefix(s, "APP_")), "_", ".", -1)
	}), nil); err != nil {
		return nil, fmt.Errorf("error loading env: %w", err)
	}

	// 4. Flags
	f := flag.NewFlagSet("config", flag.ContinueOnError)
	f.String("server.host", "127.0.0.1", "server host")
	f.Int("server.port", 8080, "server port")
	f.Parse(os.Args[1:])
	if err := k.Load(posixflags.Provider(f, "."), nil); err != nil {
		return nil, fmt.Errorf("error loading flags: %w", err)
	}

	var cfg Config
	if err := k.Unmarshal("", &cfg); err != nil {
		return nil, fmt.Errorf("unmarshal error: %w", err)
	}

	// 5. Validation
	validate := validator.New()
	if err := validate.Struct(&cfg); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	return &cfg, nil
}